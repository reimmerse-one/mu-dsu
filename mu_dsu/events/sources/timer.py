"""Timer event source — periodic or bounded tick events."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from mu_dsu.events.types import NORMAL, Event, EventPriority


class TimerSource:
    """Emits periodic timer events."""

    def __init__(
        self,
        interval: float,
        event_type: str = "timer.tick",
        priority: EventPriority = NORMAL,
        payload_factory: Callable[[], dict[str, Any]] | None = None,
        max_ticks: int | None = None,
    ) -> None:
        self._interval = interval
        self._event_type = event_type
        self._priority = priority
        self._payload_factory = payload_factory
        self._max_ticks = max_ticks
        self._running = False
        self._tick_count = 0

    @property
    def name(self) -> str:
        return f"timer({self._event_type})"

    @property
    def tick_count(self) -> int:
        return self._tick_count

    async def start(self, emit: Callable[[Event], None]) -> None:
        self._running = True
        self._tick_count = 0
        while self._running:
            await asyncio.sleep(self._interval)
            if not self._running:
                break
            self._tick_count += 1
            payload = self._payload_factory() if self._payload_factory else {"tick": self._tick_count}
            emit(Event(
                type=self._event_type,
                source=self.name,
                payload=payload,
                priority=self._priority,
            ))
            if self._max_ticks is not None and self._tick_count >= self._max_ticks:
                break

    async def stop(self) -> None:
        self._running = False
