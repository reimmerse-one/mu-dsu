"""Tree-walking interpreter with pluggable semantic actions.

Visits Lark parse trees and dispatches to SemanticAction handlers
based on node type, role, and phase. Actions can be swapped between
visits — the key mechanism enabling μ-DSU runtime adaptation.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from lark import Token, Tree

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.environment import Environment


@dataclass
class Context:
    """Passed to semantic action handlers."""

    env: Environment
    interpreter: Interpreter
    metadata: dict[str, Any] = field(default_factory=dict)


class Interpreter:
    """Tree-walking interpreter with pluggable semantic actions.

    Corresponds to component ② in Fig. 3 of the paper.
    The interpreter retains the parse tree so the micro-language adapter
    can inspect and modify it at runtime.
    """

    def __init__(
        self,
        composer: GrammarComposer,
        actions: ActionRegistry,
        env: Environment | None = None,
    ) -> None:
        self._composer = composer
        self._actions = actions
        self._env = env or Environment()
        self._parser = None
        self._parse_tree: Tree | None = None
        self._current_role: str = "execution"
        self._paused: bool = False
        self._running: bool = False
        self._pausing_thread: threading.Thread | None = None
        self._resume_signal = threading.Event()
        self._resume_signal.set()

    @property
    def composer(self) -> GrammarComposer:
        return self._composer

    @property
    def actions(self) -> ActionRegistry:
        return self._actions

    @property
    def env(self) -> Environment:
        return self._env

    @property
    def parse_tree(self) -> Tree | None:
        return self._parse_tree

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_running(self) -> bool:
        """True while run() is executing the parse tree."""
        return self._running

    def pause(self) -> None:
        """Pause interpretation. Called by EventManager before adaptation.

        A running interpretation blocks at its next update point (the next
        node visit) until resume() is called — per Sect. 4.2 of the paper,
        each event 'blocks the interpretation of the application' and
        'interpretation is resumed from the point of the previous
        suspension, but using the adapted interpreter'.
        """
        self._paused = True
        self._pausing_thread = threading.current_thread()
        self._resume_signal.clear()

    def resume(self) -> None:
        """Resume interpretation after adaptation."""
        self._paused = False
        self._pausing_thread = None
        self._resume_signal.set()

    def load(self, source: str) -> Tree:
        """Parse source into an AST. The parse tree is retained for adaptation."""
        parser = self._ensure_parser()
        self._parse_tree = parser.parse(source)
        return self._parse_tree

    def run(
        self,
        source: str | None = None,
        role: str = "execution",
        subtree: Tree | None = None,
    ) -> Any:
        """Execute a program.

        If source is given, parse it first. Otherwise use the previously loaded tree.
        If subtree is given, execute from that node instead of the root.
        """
        if source is not None:
            self.load(source)
        target = subtree if subtree is not None else self._parse_tree
        if target is None:
            raise RuntimeError("No program loaded — call load() or pass source to run()")
        self._current_role = role
        already_running = self._running  # redo re-enters run() mid-execution
        self._running = True
        try:
            return self._visit(target)
        finally:
            self._running = already_running

    def invalidate_parser(self) -> None:
        """Force parser rebuild on next parse — called after slice swap."""
        self._parser = None
        self._composer.invalidate()

    def _ensure_parser(self) -> Any:
        if self._parser is None:
            self._parser = self._composer.build_parser()
        return self._parser

    def _visit(self, node: Tree | Token) -> Any:
        """Core dispatch: visit a node, executing semantic actions by phase.

        Every node visit is an update point: if the interpreter was paused
        (from another thread), execution blocks here until resume(), then
        continues with whatever actions/slices the adaptation installed.
        """
        if self._paused and threading.current_thread() is not self._pausing_thread:
            self._resume_signal.wait(timeout=30.0)

        if isinstance(node, Token):
            return self._visit_token(node)

        ctx = Context(env=self._env, interpreter=self)
        visit_fn = self._visit
        role = self._current_role

        # Phase 1: before
        for action in self._actions.get_actions(node.data, role):
            if action.phase == "before":
                action.handler(node, ctx)

        # Phase 2: replace (or default child visitation)
        replace = self._actions.get_replace_action(node.data, role)
        if replace is not None:
            result = replace.handler(node, ctx, visit_fn)
        else:
            # Default: visit children, return last non-None result
            result = self._visit_children_default(node)

        # Phase 3: after
        for action in self._actions.get_actions(node.data, role):
            if action.phase == "after":
                result = action.handler(node, ctx, visit_fn, result)

        return result

    def _visit_children_default(self, node: Tree) -> Any:
        """Visit all children, return last non-None result."""
        result: Any = None
        for child in node.children:
            child_result = self._visit(child)
            if child_result is not None:
                result = child_result
        return result

    def _visit_token(self, token: Token) -> Any:
        """Default token handling."""
        if token.type == "NUMBER":
            return int(token)
        if token.type in ("FLOAT", "DECIMAL"):
            return float(token)
        return str(token)
