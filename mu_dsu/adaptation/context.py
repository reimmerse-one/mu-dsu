"""Context resolution — maps symbolic names in μDA scripts to concrete objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from mu_dsu.core.interpreter import Interpreter
from mu_dsu.core.slice import LanguageSlice, SemanticAction
from mu_dsu.adaptation.operations import (
    ActionBinding,
    ContextDef,
    NonterminalBinding,
    SliceBinding,
)


@dataclass
class ResolvedContext:
    """Resolved bindings from a μDA context section."""
    slices: dict[str, LanguageSlice] = field(default_factory=dict)
    nonterminals: dict[str, str] = field(default_factory=dict)  # name -> node_type
    actions: dict[str, SemanticAction] = field(default_factory=dict)


class ContextResolver:
    """Resolves μDA context definitions against a running interpreter.

    Slice lookup order:
    1. slice_registry (external, for new/replacement slices)
    2. interpreter.composer.slices (currently registered slices)
    """

    def __init__(
        self,
        interpreter: Interpreter,
        slice_registry: dict[str, LanguageSlice | Callable[[], LanguageSlice]] | None = None,
    ) -> None:
        self._interpreter = interpreter
        self._slice_registry = slice_registry or {}

    def resolve(self, context_defs: list[ContextDef]) -> ResolvedContext:
        ctx = ResolvedContext()
        for defn in context_defs:
            if isinstance(defn, SliceBinding):
                self._resolve_slice(defn, ctx)
            elif isinstance(defn, NonterminalBinding):
                self._resolve_nonterminal(defn, ctx)
            elif isinstance(defn, ActionBinding):
                self._resolve_action(defn, ctx)
        return ctx

    def _resolve_slice(self, defn: SliceBinding, ctx: ResolvedContext) -> None:
        sl = self._find_slice(defn.qualified_name)
        for name in defn.names:
            ctx.slices[name] = sl

    def _resolve_nonterminal(self, defn: NonterminalBinding, ctx: ResolvedContext) -> None:
        # Map each non-placeholder name to the rule_name (node_type in Lark)
        for name in defn.names:
            if name != "_":
                ctx.nonterminals[name] = defn.rule_name

    def _resolve_action(self, defn: ActionBinding, ctx: ResolvedContext) -> None:
        sl = self._find_slice(defn.module_name)
        for action in sl.actions:
            if action.node_type == defn.nonterminal and action.role == defn.role:
                ctx.actions[defn.name] = action
                return
        raise KeyError(
            f"Action for nonterminal {defn.nonterminal!r} role {defn.role!r} "
            f"not found in slice {defn.module_name!r}"
        )

    def _find_slice(self, qualified_name: str) -> LanguageSlice:
        # Check external registry first
        if qualified_name in self._slice_registry:
            entry = self._slice_registry[qualified_name]
            if callable(entry) and not isinstance(entry, LanguageSlice):
                return entry()
            return entry  # type: ignore[return-value]

        # Check composer's registered slices
        composer_slices = self._interpreter.composer.slices
        if qualified_name in composer_slices:
            return composer_slices[qualified_name]

        raise KeyError(f"Slice {qualified_name!r} not found in registry or composer")
