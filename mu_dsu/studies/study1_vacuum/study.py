"""Study 1: Vacuum Cleaner Stand-by Adaptation (Sect. 2.3, 3.2).

Demonstrates seamless adaptation — the program text is unchanged,
but the interpreter's semantics evolve at runtime via slice replacement.
"""

from __future__ import annotations

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.events.manager import EventManager
from mu_dsu.events.sources.runtime import RuntimeCondition, RuntimeSource
from mu_dsu.events.types import Event, Subscription
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.runner import StateMachineRunner
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice
from mu_dsu.studies.study1_vacuum.adaptation_script import STANDBY_ADAPTATION


class VacuumCleanerStudy:
    """Orchestrates the vacuum cleaner stand-by adaptation study."""

    def __init__(self) -> None:
        composer, actions = compose_hooverlang()
        self.interpreter = Interpreter(composer, actions)
        self.interpreter.env.set_global("get.click", lambda: False)
        self.adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
        self.runner = StateMachineRunner(self.interpreter)
        self.program_text = DEFAULT_PROGRAM

    def load(self) -> None:
        """Parse and run the default vacuum cleaner program."""
        self.runner.load(self.program_text)

    def run_before(self, click_sequence: list[bool]) -> list[str]:
        """Exercise the default state machine, return state trace."""
        idx = 0

        def next_click():
            nonlocal idx
            if idx < len(click_sequence):
                val = click_sequence[idx]
                idx += 1
                return val
            return False

        self.interpreter.env.set_global("get.click", next_click)
        return self.runner.run_steps(len(click_sequence))

    def trigger_adaptation(self) -> bool:
        """Execute μDA adaptation synchronously."""
        result = self.adapter.adapt(STANDBY_ADAPTATION, self.interpreter)
        return result.success

    def trigger_adaptation_via_event(self) -> bool:
        """Execute adaptation via event manager (runtime condition)."""
        mgr = EventManager(interpreter=self.interpreter, adapter=self.adapter)
        mgr.subscribe(Subscription(
            event_pattern="runtime.inactivity",
            adaptation_script=STANDBY_ADAPTATION,
        ))
        # Simulate: fire event directly
        self.interpreter.env.set("__inactive__", True)
        results = mgr.process_event(Event(
            type="runtime.inactivity", source="runtime",
        ))
        return len(results) > 0 and results[0].success

    @property
    def has_standby_semantics(self) -> bool:
        return (
            self.interpreter.env.has("__sm_standby_enabled__")
            and self.interpreter.env.get("__sm_standby_enabled__") is True
        )
