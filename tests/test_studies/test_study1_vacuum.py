"""Study 1 tests: Vacuum Cleaner Stand-by Adaptation."""

from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.studies.study1_vacuum.study import VacuumCleanerStudy


class TestVacuumCleanerStudy:
    def test_before_adaptation_two_states(self):
        study = VacuumCleanerStudy()
        study.load()
        assert set(study.runner.states.keys()) == {"on", "off"}

    def test_before_adaptation_toggle(self):
        study = VacuumCleanerStudy()
        study.load()
        trace = study.run_before([True, True, True, True])
        assert trace == ["off", "on", "off", "on"]

    def test_no_standby_before_adaptation(self):
        study = VacuumCleanerStudy()
        study.load()
        assert not study.has_standby_semantics

    def test_adaptation_succeeds(self):
        study = VacuumCleanerStudy()
        study.load()
        assert study.trigger_adaptation()

    def test_after_adaptation_standby_enabled(self):
        study = VacuumCleanerStudy()
        study.load()
        study.trigger_adaptation()
        assert study.has_standby_semantics

    def test_program_text_unchanged(self):
        study = VacuumCleanerStudy()
        study.load()
        text_before = study.program_text
        study.trigger_adaptation()
        assert study.program_text == text_before
        assert study.program_text == DEFAULT_PROGRAM

    def test_event_triggered_adaptation(self):
        study = VacuumCleanerStudy()
        study.load()
        assert not study.has_standby_semantics
        assert study.trigger_adaptation_via_event()
        assert study.has_standby_semantics

    def test_state_preserved_through_adaptation(self):
        study = VacuumCleanerStudy()
        study.load()
        study.interpreter.env.set("user_data", 42)
        study.trigger_adaptation()
        assert study.interpreter.env.get("user_data") == 42
