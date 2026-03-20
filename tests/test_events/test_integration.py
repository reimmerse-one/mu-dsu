"""Phase 4 validation: event triggers adaptation on HooverLang interpreter.

Proves the full pipeline: source → event → bus → manager → adapter → interpreter.
"""

import asyncio
import tempfile
from pathlib import Path

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.events.manager import EventManager
from mu_dsu.events.sources.file_watch import FileWatchSource
from mu_dsu.events.sources.runtime import RuntimeCondition, RuntimeSource
from mu_dsu.events.sources.timer import TimerSource
from mu_dsu.events.types import Event, Subscription
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.runner import StateMachineRunner
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice


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


def _make_hooverlang():
    composer, actions = compose_hooverlang()
    interp = Interpreter(composer, actions)
    interp.env.set_global("get.click", lambda: False)
    interp.run(DEFAULT_PROGRAM)
    return interp


class TestEventTriggersAdaptation:
    """Full pipeline: event → adaptation → interpreter behaviour change."""

    def test_timer_event_triggers_standby_adaptation(self):
        """Timer ticks → μDA adaptation → interpreter has standby semantics."""
        interp = _make_hooverlang()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="timer.tick",
            adaptation_script=STANDBY_SCRIPT,
        ))
        mgr.register_source(TimerSource(interval=0.02, max_ticks=1))

        assert not interp.env.has("__sm_standby_enabled__")
        asyncio.run(mgr.run(timeout=0.5))

        assert interp.env.get("__sm_standby_enabled__") is True
        assert mgr.results[0].success

    def test_file_change_triggers_adaptation(self, tmp_path):
        """Config file change → μDA adaptation → interpreter updated."""
        config = tmp_path / "profile.cfg"
        config.write_text("healthy")

        interp = _make_hooverlang()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="file.changed",
            adaptation_script=STANDBY_SCRIPT,
        ))
        mgr.register_source(FileWatchSource(paths=[config], poll_interval=0.02))

        async def run():
            task = asyncio.create_task(mgr.run())
            await asyncio.sleep(0.05)
            config.write_text("blind")  # Trigger file change
            await asyncio.sleep(0.2)
            await mgr.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        assert interp.env.get("__sm_standby_enabled__") is True

    def test_runtime_condition_triggers_adaptation(self):
        """Runtime condition (inactivity) → adaptation."""
        interp = _make_hooverlang()
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })

        cond = RuntimeCondition(
            name="inactivity",
            check=lambda i: i.env.has("__inactive__") and i.env.get("__inactive__"),
            event_type="runtime.inactivity",
        )
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="runtime.inactivity",
            adaptation_script=STANDBY_SCRIPT,
        ))
        mgr.register_source(RuntimeSource(interp, [cond], poll_interval=0.02))

        async def run():
            task = asyncio.create_task(mgr.run())
            await asyncio.sleep(0.05)
            interp.env.set("__inactive__", True)  # Trigger condition
            await asyncio.sleep(0.2)
            await mgr.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        assert interp.env.get("__sm_standby_enabled__") is True


class TestAdaptationPreservesState:
    """Hot-reload: adaptation changes semantics but preserves runtime state."""

    def test_state_preserved_after_adaptation(self):
        """Runner state survives adaptation — app code unchanged."""
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: True)
        runner = StateMachineRunner(interp)
        runner.load(DEFAULT_PROGRAM)

        # Run a few steps
        runner.step()  # on → off
        assert runner.current_state == "off"

        # Set a custom variable to prove state persists
        interp.env.set("user_data", 42)

        # Adapt via event
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        mgr = EventManager(interpreter=interp, adapter=adapter)
        mgr.subscribe(Subscription(
            event_pattern="upgrade",
            adaptation_script=STANDBY_SCRIPT,
        ))

        mgr.process_event(Event(type="upgrade", source="test"))

        # State preserved
        assert interp.env.get("user_data") == 42
        # Semantics changed
        assert interp.env.get("__sm_standby_enabled__") is True
