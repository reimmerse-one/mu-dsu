"""Tests for HooverLang execution — Listing 2b (extended with stand-by)."""

from mu_dsu.languages.state_machine import create_runner
from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM


def _setup_runner(click=False, activity=False, inactivity=False):
    """Create a runner with controllable event sources."""
    runner = create_runner()
    runner._interp.env.set_global("get.click", lambda: click)
    runner._interp.env.set_global("get.activity", lambda: activity)
    runner._interp.env.set_global("get.time", lambda: inactivity)
    runner.load(STANDBY_PROGRAM)
    return runner


class TestStandbyProgram:
    """Vacuum cleaner extended behaviour with counter and stand-by state."""

    def test_counter_initialized(self):
        runner = _setup_runner()
        assert runner._interp.env.get("t") == 0

    def test_three_states_defined(self):
        runner = _setup_runner()
        assert set(runner.states.keys()) == {"on", "off", "stand-by"}

    def test_four_events_defined(self):
        runner = _setup_runner()
        assert set(runner.events.keys()) == {"click", "elapsed", "activity", "inactivity"}

    def test_on_state_resets_counter(self):
        """Entering 'on' state should reset t to 0."""
        runner = _setup_runner()
        # Manually set t to prove it gets reset
        runner._interp.env.set("t", 42)
        runner._enter_state("on")
        assert runner._interp.env.get("t") == 0

    def test_standby_increments_counter(self):
        """Entering 'stand-by' state should increment t."""
        runner = _setup_runner()
        runner._interp.env.set("t", 5)
        runner._enter_state("stand-by")
        assert runner._interp.env.get("t") == 6

    def test_inactivity_transitions_to_standby(self):
        """on -> stand-by when inactivity event fires."""
        runner = _setup_runner(inactivity=True)
        result = runner.step()
        assert result == "stand-by"

    def test_click_from_on_transitions_to_off(self):
        runner = _setup_runner(click=True)
        result = runner.step()
        assert result == "off"

    def test_standby_to_off_after_elapsed(self):
        """stand-by -> off when t > 10."""
        runner = _setup_runner()
        # Manually enter stand-by with t > 10
        runner._interp.env.set("t", 11)
        runner._current_state = "stand-by"
        result = runner.step()
        # elapsed (t > 10) should fire -> off
        assert result == "off"

    def test_standby_to_on_on_activity(self):
        """stand-by -> on when activity detected."""
        runner = _setup_runner(activity=True)
        runner._current_state = "stand-by"
        runner._interp.env.set("t", 3)
        result = runner.step()
        assert result == "on"

    def test_full_standby_scenario(self):
        """on -> stand-by (repeat until elapsed) -> off.

        Simulates: no activity for 12 cycles, then times out.
        """
        runner = create_runner()
        runner._interp.env.set_global("get.click", lambda: False)
        runner._interp.env.set_global("get.activity", lambda: False)
        # inactivity fires every step
        runner._interp.env.set_global("get.time", lambda: True)
        runner.load(STANDBY_PROGRAM)

        assert runner.current_state == "on"

        # Step 1: on -> stand-by (inactivity fires)
        result = runner.step()
        assert result == "stand-by"

        # Steps 2-11: stand-by -> stand-by (inactivity fires, t increments)
        # t starts at 1 after first stand-by entry, increments each re-entry
        for i in range(10):
            result = runner.step()
            assert result == "stand-by", f"Expected stand-by at step {i+2}"

        # Step 12: t should now be > 10, elapsed fires -> off
        # But inactivity is checked before elapsed in the transition list
        # So we need to check the transition order
        # In the program: stand-by { click => off ; elapsed => off ; inactivity => stand-by ; activity => on }
        # elapsed is checked before inactivity, so when t > 10, elapsed fires first
        result = runner.step()
        assert result == "off"
