"""Tests for HooverLang execution — Listing 2a (default behaviour)."""

from mu_dsu.languages.state_machine import create_runner
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM


def _make_click_queue(*clicks):
    """Create a click event source from a sequence of True/False values."""
    queue = list(clicks)
    return lambda: queue.pop(0) if queue else False


class TestDefaultProgram:
    """Vacuum cleaner default behaviour: on/off toggle via click."""

    def test_load_populates_states(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner.load(DEFAULT_PROGRAM)
        assert "on" in runner.states
        assert "off" in runner.states

    def test_load_populates_events(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner.load(DEFAULT_PROGRAM)
        assert "click" in runner.events

    def test_load_populates_transitions(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner.load(DEFAULT_PROGRAM)
        assert "on" in runner.transitions
        assert "off" in runner.transitions
        assert runner.transitions["on"] == [("click", "off")]
        assert runner.transitions["off"] == [("click", "on")]

    def test_starts_in_first_state(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner.load(DEFAULT_PROGRAM)
        assert runner.current_state == "on"

    def test_click_transitions_on_to_off(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", _make_click_queue(False, True))
        runner.load(DEFAULT_PROGRAM)
        assert runner.current_state == "on"

        result = runner.step()
        assert result is None  # click=False, no transition

        result = runner.step()
        assert result == "off"  # click=True, transition to off

    def test_click_transitions_off_to_on(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", _make_click_queue(True, True))
        runner.load(DEFAULT_PROGRAM)
        assert runner.current_state == "on"

        runner.step()  # on -> off
        assert runner.current_state == "off"

        runner.step()  # off -> on
        assert runner.current_state == "on"

    def test_full_cycle(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", _make_click_queue(True, True, True, True))
        runner.load(DEFAULT_PROGRAM)

        states = runner.run_steps(4)
        assert states == ["off", "on", "off", "on"]

    def test_no_transition_when_no_events(self):
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner.load(DEFAULT_PROGRAM)

        result = runner.step()
        assert result is None
        assert runner.current_state == "on"
