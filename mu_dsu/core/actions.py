"""Semantic action registry.

Maps AST node types to semantic actions, organized by role.
Supports dynamic addition/removal/replacement — the key mechanism
enabling μ-DSU runtime adaptation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from mu_dsu.core.slice import LanguageSlice, SemanticAction


class ActionRegistry:
    """Registry of semantic actions, keyed by (node_type, role).

    Actions are ordered: within the same (node_type, role), they execute
    in registration order. The before/replace/after phase determines
    *when* each action fires relative to child visitation.
    """

    def __init__(self) -> None:
        # node_type -> role -> [actions]
        self._actions: dict[str, dict[str, list[SemanticAction]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def register(self, action: SemanticAction) -> None:
        """Add an action to the registry."""
        self._actions[action.node_type][action.role].append(action)

    def register_all(self, actions: Iterable[SemanticAction]) -> None:
        """Register multiple actions."""
        for action in actions:
            self.register(action)

    def unregister(
        self, node_type: str, role: str, *, action_id: str | None = None
    ) -> SemanticAction | None:
        """Remove an action.

        If action_id is given, remove that specific action.
        Otherwise remove the last-registered action for (node_type, role).
        Returns the removed action, or None if nothing matched.
        """
        actions = self._actions[node_type][role]
        if not actions:
            return None

        if action_id is not None:
            for i, a in enumerate(actions):
                if a.id == action_id:
                    return actions.pop(i)
            return None

        return actions.pop()

    def get_actions(self, node_type: str, role: str) -> list[SemanticAction]:
        """Return all actions for (node_type, role). Empty list if none."""
        return self._actions[node_type][role]

    def get_replace_action(
        self, node_type: str, role: str
    ) -> SemanticAction | None:
        """Return the last phase='replace' action, or None."""
        for action in reversed(self._actions[node_type][role]):
            if action.phase == "replace":
                return action
        return None

    def replace_action(
        self,
        node_type: str,
        role: str,
        old_id: str,
        new_action: SemanticAction,
    ) -> SemanticAction:
        """Replace an action in-place (same position in the list).

        Raises KeyError if old_id is not found.
        """
        actions = self._actions[node_type][role]
        for i, a in enumerate(actions):
            if a.id == old_id:
                old = actions[i]
                actions[i] = new_action
                return old
        raise KeyError(
            f"Action {old_id!r} not found for ({node_type!r}, {role!r})"
        )

    def clear(self) -> None:
        """Remove all registered actions."""
        self._actions.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a serializable snapshot of current state."""
        return {
            node_type: {
                role: [a.id for a in actions]
                for role, actions in roles.items()
            }
            for node_type, roles in self._actions.items()
        }

    def load_from_slice(self, sl: LanguageSlice) -> None:
        """Register all actions from a slice."""
        self.register_all(sl.actions)

    def unload_slice(self, sl: LanguageSlice) -> None:
        """Unregister all actions that came from a given slice."""
        for action in sl.actions:
            self.unregister(action.node_type, action.role, action_id=action.id)
