"""Tests for RuntimeSource."""

import asyncio

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.core.slice import LanguageSlice, SyntaxDefinition
from mu_dsu.events.sources.runtime import RuntimeCondition, RuntimeSource
from mu_dsu.events.types import Event


def _make_minimal_interpreter():
    composer = GrammarComposer()
    composer.register(LanguageSlice(
        name="min",
        syntax=SyntaxDefinition(
            rules="start: NUMBER",
            terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
        ),
    ))
    return Interpreter(composer, ActionRegistry())


class TestRuntimeSource:
    def test_condition_triggers(self):
        interp = _make_minimal_interpreter()
        interp.env.set("flag", False)
        events: list[Event] = []

        cond = RuntimeCondition(
            name="flag_check",
            check=lambda i: i.env.has("flag") and i.env.get("flag") is True,
            event_type="runtime.flag",
        )
        source = RuntimeSource(interp, [cond], poll_interval=0.02)

        async def run():
            task = asyncio.create_task(source.start(events.append))
            await asyncio.sleep(0.05)
            interp.env.set("flag", True)  # Trigger the condition
            await asyncio.sleep(0.1)
            await source.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        assert len(events) >= 1
        assert events[0].type == "runtime.flag"

    def test_edge_trigger_only_fires_once(self):
        """Condition that stays True should only fire once (edge-triggered)."""
        interp = _make_minimal_interpreter()
        interp.env.set("flag", True)  # Already True from start
        events: list[Event] = []

        cond = RuntimeCondition(
            name="steady",
            check=lambda i: i.env.get("flag") is True,
            event_type="runtime.steady",
        )
        source = RuntimeSource(interp, [cond], poll_interval=0.02)

        async def run():
            task = asyncio.create_task(source.start(events.append))
            # First poll: prev=False, current=True -> fires
            # Second poll: prev=True, current=True -> does NOT fire
            await asyncio.sleep(0.15)
            await source.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        # Should fire exactly once (edge trigger on first check)
        assert len(events) == 1
