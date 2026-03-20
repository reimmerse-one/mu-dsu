"""Micro-Language Adapter — executes μDA scripts against a running interpreter.

Component ④ in Fig. 3 of the paper. Ties together the parser, context resolver,
matcher, and interpreter to perform both system-wide and localised adaptations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from mu_dsu.adaptation.context import ContextResolver, ResolvedContext
from mu_dsu.adaptation.matcher import ParseTreeMatcher
from mu_dsu.adaptation.mu_da_parser import MuDaParser
from mu_dsu.adaptation.operations import (
    AddAction,
    AdaptationResult,
    AdaptationScript,
    RedoRole,
    RemoveAction,
    ReplaceSlice,
    SetSpecialized,
    SystemWideClause,
    WhenClause,
)
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.core.slice import LanguageSlice, SemanticAction


class MicroLanguageAdapter:
    """Parses and executes μDA adaptation scripts.

    Usage:
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state.standby": standby_state_slice,
        })
        result = adapter.adapt(script_text, interpreter)
    """

    def __init__(
        self,
        slice_registry: dict[str, LanguageSlice | Callable[[], LanguageSlice]] | None = None,
    ) -> None:
        self._parser = MuDaParser()
        self._matcher = ParseTreeMatcher()
        self._slice_registry = slice_registry or {}

    def adapt(self, script: str, interpreter: Interpreter) -> AdaptationResult:
        """Parse and execute a μDA script against the interpreter."""
        parsed = self._parser.parse(script)
        resolver = ContextResolver(interpreter, self._slice_registry)
        ctx = resolver.resolve(parsed.context)

        applied: list[str] = []
        errors: list[str] = []

        for clause in parsed.clauses:
            try:
                if isinstance(clause, SystemWideClause):
                    ops = self._apply_system_wide(clause, ctx, interpreter)
                    applied.extend(ops)
                elif isinstance(clause, WhenClause):
                    ops = self._apply_localised(clause, ctx, interpreter)
                    applied.extend(ops)
            except Exception as e:
                errors.append(str(e))

        return AdaptationResult(
            success=len(errors) == 0,
            operations_applied=applied,
            errors=errors,
        )

    def adapt_from_file(self, path: str | Path, interpreter: Interpreter) -> AdaptationResult:
        return self.adapt(Path(path).read_text(), interpreter)

    def _apply_system_wide(
        self, clause: SystemWideClause, ctx: ResolvedContext, interpreter: Interpreter
    ) -> list[str]:
        applied: list[str] = []

        for op in clause.operations:
            if isinstance(op, ReplaceSlice):
                old_slice = ctx.slices[op.old_name]
                new_slice = ctx.slices[op.new_name]
                old_name = old_slice.name

                # Unload old actions, replace slice in composer, load new actions
                interpreter.actions.unload_slice(old_slice)
                interpreter.composer.replace(old_name, new_slice)
                interpreter.actions.load_from_slice(new_slice)
                interpreter.invalidate_parser()
                applied.append(f"replace_slice({old_name} -> {new_slice.name})")

            elif isinstance(op, RedoRole):
                role = op.role or "execution"
                interpreter.run(role=role)
                applied.append(f"redo(role={role})")

        return applied

    def _apply_localised(
        self, clause: WhenClause, ctx: ResolvedContext, interpreter: Interpreter
    ) -> list[str]:
        if interpreter.parse_tree is None:
            return []

        matched = self._matcher.match(clause.match_expr, interpreter.parse_tree, ctx)
        applied: list[str] = []

        for node in matched:
            for manip in clause.manipulations:
                if isinstance(manip, AddAction):
                    action = ctx.actions[manip.action_name]
                    # Wrap handler with node identity check
                    filtered = self._make_node_filtered_action(action, node)
                    interpreter.actions.register(filtered)
                    applied.append(f"add_action({action.id} to {node.data})")

                elif isinstance(manip, RemoveAction):
                    interpreter.actions.unregister(
                        node.data, manip.role, action_id=manip.action_name
                    )
                    applied.append(f"remove_action({manip.action_name} from {node.data})")

                elif isinstance(manip, SetSpecialized):
                    action = ctx.actions[manip.action_name]
                    filtered = self._make_node_filtered_action(action, node)
                    # Replace existing action for this node type
                    existing = interpreter.actions.get_replace_action(node.data, manip.role)
                    if existing:
                        # Install a dispatcher that checks node identity
                        dispatcher = self._make_dispatcher(existing, filtered, node)
                        interpreter.actions.replace_action(
                            node.data, manip.role, existing.id, dispatcher
                        )
                    else:
                        interpreter.actions.register(filtered)
                    applied.append(f"set_specialized({action.id} for {node.data})")

        return applied

    def _make_node_filtered_action(
        self, action: SemanticAction, target_node: Any
    ) -> SemanticAction:
        """Create a copy of an action that only fires for a specific node."""
        original_handler = action.handler
        target = target_node

        def filtered_handler(node, ctx, visit, *args):
            if node is target:
                return original_handler(node, ctx, visit, *args)
            return None

        return SemanticAction(
            node_type=action.node_type,
            role=action.role,
            phase=action.phase,
            handler=filtered_handler,
            id=f"{action.id}@{id(target_node)}",
        )

    def _make_dispatcher(
        self,
        original: SemanticAction,
        specialized: SemanticAction,
        target_node: Any,
    ) -> SemanticAction:
        """Create a dispatcher: use specialized for target node, original for others."""
        orig_handler = original.handler
        spec_handler = specialized.handler
        target = target_node

        def dispatch(node, ctx, visit, *args):
            if node is target:
                return spec_handler(node, ctx, visit, *args)
            return orig_handler(node, ctx, visit, *args)

        return SemanticAction(
            node_type=original.node_type,
            role=original.role,
            phase=original.phase,
            handler=dispatch,
            id=original.id,
        )
