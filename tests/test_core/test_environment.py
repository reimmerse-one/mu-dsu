"""Tests for Environment."""

import pytest

from mu_dsu.core.environment import Environment


class TestEnvironment:
    def test_set_and_get(self):
        env = Environment()
        env.set("x", 42)
        assert env.get("x") == 42

    def test_undefined_raises(self):
        env = Environment()
        with pytest.raises(NameError, match="Undefined variable 'x'"):
            env.get("x")

    def test_scope_shadowing(self):
        env = Environment()
        env.set("x", 1)
        env.push_scope()
        env.set("x", 2)
        assert env.get("x") == 2
        env.pop_scope()
        assert env.get("x") == 1

    def test_pop_last_scope_raises(self):
        env = Environment()
        with pytest.raises(RuntimeError, match="Cannot pop the last scope"):
            env.pop_scope()

    def test_globals_accessible_from_any_depth(self):
        env = Environment(globals={"PI": 3.14})
        assert env.get("PI") == 3.14
        env.push_scope()
        env.push_scope()
        assert env.get("PI") == 3.14

    def test_set_global(self):
        env = Environment()
        env.set_global("G", 100)
        assert env.get("G") == 100

    def test_has(self):
        env = Environment()
        assert not env.has("x")
        env.set("x", 1)
        assert env.has("x")

    def test_has_global(self):
        env = Environment(globals={"G": 1})
        assert env.has("G")

    def test_current_scope_returns_copy(self):
        env = Environment()
        env.set("x", 1)
        scope = env.current_scope()
        scope["x"] = 999
        assert env.get("x") == 1  # Original unchanged

    def test_push_scope_with_bindings(self):
        env = Environment()
        env.push_scope({"a": 10, "b": 20})
        assert env.get("a") == 10
        assert env.get("b") == 20
