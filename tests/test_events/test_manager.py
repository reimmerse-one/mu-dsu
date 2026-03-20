"""Tests for EventManager."""

import asyncio

import pytest

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.events.manager import EventManager
from mu_dsu.events.types import Event, Subscription
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice


def _make_hooverlang_interpreter():
    composer, actions = compose_hooverlang()
    interp = Interpreter(composer, actions)
    interp.env.set_global("get.click", lambda: False)
    interp.run(DEFAULT_PROGRAM)
    return interp


STANDBY_SCRIPT = """
context {
    slice old: sm.state;
    slice new: sm.state_standby;
}
system-wide {
    replace slice old with new;
    redo role execution;
}
"""


class TestEventManagerSync:
    """Synchronous tests using process_event()."""

    def test_process_event_triggers_adaptation(self):
        interp = _make_hooverlang_interpreter()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="config.changed",
            adaptation_script=STANDBY_SCRIPT,
        ))

        results = mgr.process_event(Event(type="config.changed", source="test"))
        assert len(results) == 1
        assert results[0].success
        assert interp.env.get("__sm_standby_enabled__") is True

    def test_pause_resume_during_adaptation(self):
        interp = _make_hooverlang_interpreter()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="e",
            adaptation_script=STANDBY_SCRIPT,
        ))

        assert not interp.is_paused
        mgr.process_event(Event(type="e", source="s"))
        # After processing, interpreter should be resumed
        assert not interp.is_paused

    def test_no_match_no_adaptation(self):
        interp = _make_hooverlang_interpreter()
        adapter = MicroLanguageAdapter()
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(event_pattern="x", adaptation_script=""))

        results = mgr.process_event(Event(type="y", source="s"))
        assert results == []

    def test_no_interpreter_returns_error(self):
        mgr = EventManager()
        mgr.subscribe(Subscription(event_pattern="e", adaptation_script="redo;"))
        results = mgr.process_event(Event(type="e", source="s"))
        assert len(results) == 1
        assert not results[0].success


class TestEventManagerAsync:
    """Async tests using run() with timeout."""

    def test_timer_triggers_adaptation(self):
        from mu_dsu.events.sources.timer import TimerSource

        interp = _make_hooverlang_interpreter()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="timer.tick",
            adaptation_script=STANDBY_SCRIPT,
        ))
        mgr.register_source(TimerSource(interval=0.02, max_ticks=1))

        asyncio.run(mgr.run(timeout=0.5))

        assert len(mgr.results) >= 1
        assert mgr.results[0].success
        assert interp.env.get("__sm_standby_enabled__") is True

    def test_run_with_no_events_stops_on_timeout(self):
        mgr = EventManager()
        asyncio.run(mgr.run(timeout=0.1))
        assert mgr.results == []
