"""Grammar composer — merges slice grammars into a single Lark grammar.

Handles rule merging, conflict detection, dependency ordering,
and parser construction. The core of modular language development.
"""

from __future__ import annotations

import re
from typing import Any

import lark

from mu_dsu.core.slice import LanguageSlice

# Matches a Lark rule definition: optional '?', rule name, then ':'
_RULE_HEAD_RE = re.compile(r"^\s*(\??\s*\w+)\s*:", re.MULTILINE)
# Matches %import / %ignore directives
_DIRECTIVE_RE = re.compile(r"^\s*(%(?:import|ignore)\s+.+)$", re.MULTILINE)


class SliceDependencyError(Exception):
    """Missing or circular slice dependencies."""


class SliceConflictError(Exception):
    """Irreconcilable grammar rule conflicts."""


class GrammarComposer:
    """Composes a complete Lark grammar from registered LanguageSlice objects.

    Slice grammars are merged: if multiple slices define the same rule name,
    their alternatives are combined with '|'. Terminals and directives
    (%import, %ignore) are deduplicated.
    """

    def __init__(self) -> None:
        self._slices: dict[str, LanguageSlice] = {}
        self._parser_cache: lark.Lark | None = None
        self._grammar_cache: str | None = None

    @property
    def slices(self) -> dict[str, LanguageSlice]:
        """Read-only access to registered slices."""
        return dict(self._slices)

    def register(self, sl: LanguageSlice) -> None:
        """Add a slice. Dependencies must already be registered."""
        for dep in sl.dependencies:
            if dep not in self._slices:
                raise SliceDependencyError(
                    f"Slice {sl.name!r} depends on {dep!r}, which is not registered"
                )
        if sl.name in self._slices:
            raise ValueError(f"Slice {sl.name!r} is already registered")
        self._slices[sl.name] = sl
        self._invalidate()

    def unregister(self, name: str) -> LanguageSlice:
        """Remove a slice. Fails if other slices depend on it."""
        if name not in self._slices:
            raise KeyError(f"Slice {name!r} is not registered")

        # Check no other slice depends on this one
        dependents = [
            s.name for s in self._slices.values()
            if name in s.dependencies and s.name != name
        ]
        if dependents:
            raise ValueError(
                f"Cannot remove {name!r}: slices {dependents} depend on it"
            )

        sl = self._slices.pop(name)
        self._invalidate()
        return sl

    def replace(self, old_name: str, new_slice: LanguageSlice) -> LanguageSlice:
        """Atomic slice replacement with rollback on failure.

        Unlike unregister(), this bypasses the dependency check because
        the new slice fulfills the same contract as the old one.
        """
        if old_name not in self._slices:
            raise KeyError(f"Slice {old_name!r} is not registered")

        old = self._slices.pop(old_name)
        self._invalidate()
        try:
            self.register(new_slice)
        except Exception:
            # Rollback
            self._slices[old.name] = old
            self._invalidate()
            raise
        return old

    def compose(self) -> str:
        """Merge all slice grammars into a single Lark grammar string."""
        if self._grammar_cache is not None:
            return self._grammar_cache

        if not self._slices:
            raise ValueError("No slices registered")

        ordered = self._topological_sort()
        grammar = self._merge_rules(ordered)
        self._grammar_cache = grammar
        return grammar

    def build_parser(self, **kwargs: Any) -> lark.Lark:
        """Build a Lark parser from the composed grammar."""
        if self._parser_cache is not None:
            return self._parser_cache

        grammar = self.compose()
        defaults = {"parser": "earley", "ambiguity": "resolve"}
        defaults.update(kwargs)
        self._parser_cache = lark.Lark(grammar, **defaults)
        return self._parser_cache

    def invalidate(self) -> None:
        """Public cache invalidation (called by interpreter after adaptation)."""
        self._invalidate()

    def _invalidate(self) -> None:
        self._parser_cache = None
        self._grammar_cache = None

    def _topological_sort(self) -> list[LanguageSlice]:
        """Sort slices so dependencies come before dependents."""
        visited: set[str] = set()
        result: list[LanguageSlice] = []
        visiting: set[str] = set()  # For cycle detection

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise SliceDependencyError(f"Circular dependency involving {name!r}")
            visiting.add(name)
            sl = self._slices[name]
            for dep in sl.dependencies:
                if dep in self._slices:
                    visit(dep)
            visiting.discard(name)
            visited.add(name)
            result.append(sl)

        for name in self._slices:
            visit(name)

        return result

    def _merge_rules(self, slices: list[LanguageSlice]) -> str:
        """Core merging logic: combine rules from all slices.

        If multiple slices define the same rule name, their bodies
        are merged with '|'. Directives are deduplicated.
        """
        # rule_name (with optional '?' prefix) -> list of rule bodies
        rule_bodies: dict[str, list[str]] = {}
        rule_order: list[str] = []
        directives: set[str] = set()

        for sl in slices:
            # Extract directives from both rules and terminals
            for source in (sl.syntax.rules, sl.syntax.terminals):
                for match in _DIRECTIVE_RE.finditer(source):
                    directives.add(match.group(1).strip())

            # Parse rules from syntax.rules
            for source in (sl.syntax.rules, sl.syntax.terminals):
                text = source.strip()
                clean = _DIRECTIVE_RE.sub("", text).strip()
                if not clean:
                    continue

                parsed = self._parse_rule_definitions(clean)
                for rule_name, body in parsed:
                    if rule_name not in rule_bodies:
                        rule_bodies[rule_name] = []
                        rule_order.append(rule_name)
                    rule_bodies[rule_name].append(body)

        # Build the merged grammar
        lines: list[str] = []
        for rule_name in rule_order:
            bodies = rule_bodies[rule_name]
            merged_body = "\n    | ".join(bodies)
            lines.append(f"{rule_name}: {merged_body}")

        # Add directives
        lines.append("")
        for directive in sorted(directives):
            lines.append(directive)

        return "\n".join(lines) + "\n"

    def _parse_rule_definitions(self, text: str) -> list[tuple[str, str]]:
        """Parse grammar text into (rule_name, body) pairs.

        Handles multi-line rules: a rule ends when the next rule starts
        or at end of text.
        """
        results: list[tuple[str, str]] = []
        matches = list(_RULE_HEAD_RE.finditer(text))

        for i, match in enumerate(matches):
            rule_name = match.group(1).strip()
            # Body starts after the ':'
            body_start = match.end()
            # Body ends at the next rule start or end of text
            body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[body_start:body_end].strip()
            results.append((rule_name, body))

        return results
