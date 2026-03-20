"""Runtime event source — watches interpreter state for condition changes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from mu_dsu.core.interpreter import Interpreter
from mu_dsu.events.types import NORMAL, Event, EventPriority


@dataclass
class RuntimeCondition:
    """A condition to monitor on the interpreter runtime."""
    name: str
    check: Callable[[Interpreter], bool]
    event_type: str = "runtime.condition"
    payload_factory: Callable[[Interpreter], dict[str, Any]] | None = None
    priority: EventPriority = field(default_factory=lambda: NORMAL)


class RuntimeSource:
    """Monitors interpreter state, emits events on condition edge transitions.

    Only fires when a condition transitions from False to True (edge-triggered),
    not while it remains True (level-triggered).
    """

    def __init__(
        self,
        interpreter: Interpreter,
        conditions: list[RuntimeCondition],
        poll_interval: float = 0.1,
    ) -> None:
        self._interpreter = interpreter
        self._conditions = conditions
        self._poll_interval = poll_interval
        self._running = False
        self._prev_states: dict[str, bool] = {}

    @property
    def name(self) -> str:
        return "runtime"

    async def start(self, emit: Callable[[Event], None]) -> None:
        self._running = True
        # Initialize previous states
        for cond in self._conditions:
            self._prev_states[cond.name] = False

        while self._running:
            await asyncio.sleep(self._poll_interval)
            if not self._running:
                break
            for cond in self._conditions:
                current = cond.check(self._interpreter)
                prev = self._prev_states.get(cond.name, False)
                if current and not prev:
                    # Edge trigger: False -> True
                    payload = (
                        cond.payload_factory(self._interpreter)
                        if cond.payload_factory
                        else {"condition": cond.name}
                    )
                    emit(Event(
                        type=cond.event_type,
                        source=self.name,
                        payload=payload,
                        priority=cond.priority,
                    ))
                self._prev_states[cond.name] = current

    async def stop(self) -> None:
        self._running = False
