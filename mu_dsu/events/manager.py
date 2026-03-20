"""Event Manager — async coordination layer (Component ③ in Fig. 3).

Wires event sources, the event bus, and the micro-language adapter together.
Handles the pause-adapt-resume cycle when events trigger adaptations.
"""

from __future__ import annotations

import asyncio
from typing import Any

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.adaptation.operations import AdaptationResult
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.events.bus import EventBus
from mu_dsu.events.sources.base import EventSource
from mu_dsu.events.types import Event, Subscription


class EventManager:
    """Async event-driven coordination layer.

    Lifecycle:
    1. Register sources and subscriptions
    2. Start the event loop (run())
    3. Sources emit events → bus matches subscriptions
    4. For each match: pause interpreter → run adapter → resume interpreter
    """

    def __init__(
        self,
        interpreter: Interpreter | None = None,
        adapter: MicroLanguageAdapter | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self._interpreter = interpreter
        self._adapter = adapter
        self._bus = bus or EventBus()
        self._sources: list[EventSource] = []
        self._running = False
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._results: list[AdaptationResult] = []
        self._seq = 0

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def results(self) -> list[AdaptationResult]:
        return list(self._results)

    def subscribe(self, sub: Subscription) -> str:
        """Register a subscription on the bus."""
        return self._bus.subscribe(sub)

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._bus.unsubscribe(subscription_id)

    def register_source(self, source: EventSource) -> None:
        self._sources.append(source)

    def emit_sync(self, event: Event) -> None:
        """Synchronous emit — for use from non-async contexts or sources."""
        self._event_queue.put_nowait(event)

    async def emit(self, event: Event) -> None:
        """Async emit — put event on the processing queue."""
        await self._event_queue.put(event)

    async def run(self, timeout: float | None = None) -> None:
        """Main event loop. Starts sources, processes events."""
        self._running = True
        tasks: list[asyncio.Task[Any]] = []

        # Start all sources — each calls self.emit_sync when events occur
        for source in self._sources:
            task = asyncio.create_task(source.start(self.emit_sync))
            tasks.append(task)

        # Process events from queue
        try:
            if timeout is not None:
                await asyncio.wait_for(self._process_loop(), timeout=timeout)
            else:
                await self._process_loop()
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        finally:
            await self.stop()
            # Cancel source tasks
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _process_loop(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.05)
            except asyncio.TimeoutError:
                continue

            matched = self._bus.publish(event)
            for sub in matched:
                result = self._handle_adaptation(event, sub)
                self._results.append(result)

    def _handle_adaptation(self, event: Event, sub: Subscription) -> AdaptationResult:
        """Pause → adapt → resume cycle."""
        if self._interpreter is None or self._adapter is None:
            return AdaptationResult(
                success=False,
                operations_applied=[],
                errors=["No interpreter or adapter configured"],
            )

        self._interpreter.pause()
        try:
            result = self._adapter.adapt(sub.adaptation_script, self._interpreter)
            return result
        except Exception as e:
            return AdaptationResult(
                success=False, operations_applied=[], errors=[str(e)]
            )
        finally:
            self._interpreter.resume()

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        for source in self._sources:
            await source.stop()

    def process_event(self, event: Event) -> list[AdaptationResult]:
        """Synchronous single-event processing. For testing without async."""
        matched = self._bus.publish(event)
        results = []
        for sub in matched:
            result = self._handle_adaptation(event, sub)
            results.append(result)
        return results
