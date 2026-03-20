"""Tests for ActionRegistry."""

import pytest

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def _noop(*args, **kwargs):
    pass


class TestActionRegistry:
    def test_register_and_get(self):
        reg = ActionRegistry()
        action = SemanticAction(
            node_type="add", role="execution", phase="replace", handler=_noop
        )
        reg.register(action)
        assert reg.get_actions("add", "execution") == [action]

    def test_get_empty(self):
        reg = ActionRegistry()
        assert reg.get_actions("nonexistent", "execution") == []

    def test_multiple_actions_ordering(self):
        reg = ActionRegistry()
        a1 = SemanticAction(
            node_type="x", role="exec", phase="before", handler=_noop, id="a1"
        )
        a2 = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="a2"
        )
        a3 = SemanticAction(
            node_type="x", role="exec", phase="after", handler=_noop, id="a3"
        )
        reg.register_all([a1, a2, a3])
        assert reg.get_actions("x", "exec") == [a1, a2, a3]

    def test_unregister_by_id(self):
        reg = ActionRegistry()
        a1 = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="a1"
        )
        a2 = SemanticAction(
            node_type="x", role="exec", phase="after", handler=_noop, id="a2"
        )
        reg.register_all([a1, a2])
        removed = reg.unregister("x", "exec", action_id="a1")
        assert removed is a1
        assert reg.get_actions("x", "exec") == [a2]

    def test_unregister_last(self):
        reg = ActionRegistry()
        a1 = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="a1"
        )
        a2 = SemanticAction(
            node_type="x", role="exec", phase="after", handler=_noop, id="a2"
        )
        reg.register_all([a1, a2])
        removed = reg.unregister("x", "exec")
        assert removed is a2

    def test_unregister_empty_returns_none(self):
        reg = ActionRegistry()
        assert reg.unregister("x", "exec") is None

    def test_get_replace_action(self):
        reg = ActionRegistry()
        a_before = SemanticAction(
            node_type="x", role="exec", phase="before", handler=_noop, id="b"
        )
        a_replace = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="r"
        )
        reg.register_all([a_before, a_replace])
        assert reg.get_replace_action("x", "exec") is a_replace

    def test_get_replace_action_none(self):
        reg = ActionRegistry()
        a_before = SemanticAction(
            node_type="x", role="exec", phase="before", handler=_noop, id="b"
        )
        reg.register(a_before)
        assert reg.get_replace_action("x", "exec") is None

    def test_replace_action_in_place(self):
        reg = ActionRegistry()
        old = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="old"
        )
        new = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="new"
        )
        reg.register(old)
        removed = reg.replace_action("x", "exec", "old", new)
        assert removed is old
        assert reg.get_actions("x", "exec") == [new]

    def test_replace_action_not_found(self):
        reg = ActionRegistry()
        new = SemanticAction(
            node_type="x", role="exec", phase="replace", handler=_noop, id="new"
        )
        with pytest.raises(KeyError):
            reg.replace_action("x", "exec", "nonexistent", new)

    def test_clear(self):
        reg = ActionRegistry()
        reg.register(
            SemanticAction(
                node_type="x", role="exec", phase="replace", handler=_noop
            )
        )
        reg.clear()
        assert reg.get_actions("x", "exec") == []

    def test_load_and_unload_slice(self):
        a1 = SemanticAction(
            node_type="num", role="execution", phase="replace",
            handler=_noop, id="num_exec",
        )
        sl = LanguageSlice(
            name="test.numbers",
            syntax=SyntaxDefinition(rules="atom: NUMBER"),
            actions=[a1],
        )
        reg = ActionRegistry()
        reg.load_from_slice(sl)
        assert reg.get_actions("num", "execution") == [a1]

        reg.unload_slice(sl)
        assert reg.get_actions("num", "execution") == []

    def test_snapshot(self):
        reg = ActionRegistry()
        reg.register(
            SemanticAction(
                node_type="x", role="exec", phase="replace",
                handler=_noop, id="my_action",
            )
        )
        snap = reg.snapshot()
        assert snap == {"x": {"exec": ["my_action"]}}
