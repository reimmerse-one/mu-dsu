"""EventSource protocol — base for all event sources."""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from mu_dsu.events.types import Event


@runtime_checkable
class EventSource(Protocol):
    """Protocol for event sources.

    Each source watches for some condition and emits events via a callback.
    """

    @property
    def name(self) -> str: ...

    async def start(self, emit: Callable[[Event], None]) -> None: ...

    async def stop(self) -> None: ...
