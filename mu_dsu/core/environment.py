"""Runtime environment — variable bindings, scope chain, execution state."""

from __future__ import annotations

from typing import Any


class Environment:
    """Variable bindings with lexical scope chain.

    Supports nested scopes (push/pop) for function calls and blocks,
    plus a separate global scope accessible from any depth.
    """

    def __init__(self, globals: dict[str, Any] | None = None) -> None:
        self._scopes: list[dict[str, Any]] = [{}]
        self._globals: dict[str, Any] = globals or {}
        self._metadata: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        """Look up a name: innermost scope first, then outward, then globals."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        if name in self._globals:
            return self._globals[name]
        raise NameError(f"Undefined variable {name!r}")

    def set(self, name: str, value: Any) -> None:
        """Set a variable in the innermost scope."""
        self._scopes[-1][name] = value

    def set_global(self, name: str, value: Any) -> None:
        """Set a variable in the global scope."""
        self._globals[name] = value

    def push_scope(self, bindings: dict[str, Any] | None = None) -> None:
        """Push a new scope (e.g., entering a function or block)."""
        self._scopes.append(bindings or {})

    def pop_scope(self) -> dict[str, Any]:
        """Pop the innermost scope. Cannot pop the last scope."""
        if len(self._scopes) <= 1:
            raise RuntimeError("Cannot pop the last scope")
        return self._scopes.pop()

    def has(self, name: str) -> bool:
        """Check if a name is defined in any scope or globals."""
        for scope in reversed(self._scopes):
            if name in scope:
                return True
        return name in self._globals

    def current_scope(self) -> dict[str, Any]:
        """Return a copy of the innermost scope."""
        return dict(self._scopes[-1])

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    def __repr__(self) -> str:
        scopes_repr = " -> ".join(str(s) for s in self._scopes)
        return f"Environment(scopes=[{scopes_repr}], globals={self._globals})"
