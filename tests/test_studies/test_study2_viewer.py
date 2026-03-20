"""Study 2 tests: HTML Viewer Accessibility Adaptation."""

from mu_dsu.studies.study2_viewer.adaptation_scripts import (
    HEALTHY_TO_BLIND,
    HEALTHY_TO_HYPEROPIC,
)
from mu_dsu.studies.study2_viewer.programs import VIEWER_MULTI_PRINT, VIEWER_PROGRAM
from mu_dsu.studies.study2_viewer.study import HTMLViewerStudy


class TestHealthyProfile:
    def test_prints_normally(self):
        study = HTMLViewerStudy()
        output = study.run()
        assert len(output) == 1
        assert output[0]["text"] == "Hello World"
        assert output[0]["size"] == 12
        assert output[0]["color"] == "red"
        assert output[0]["profile"] == "healthy"

    def test_no_speech(self):
        study = HTMLViewerStudy()
        study.run()
        assert study.speech_buffer == []


class TestHyperopicProfile:
    def test_enlarges_font(self):
        study = HTMLViewerStudy()
        study.run()
        study.adapt(HEALTHY_TO_HYPEROPIC)
        output = study.run()
        assert output[0]["size"] == 12 * 3  # multiplied by 3
        assert output[0]["profile"] == "hyperopic"

    def test_text_unchanged(self):
        study = HTMLViewerStudy()
        study.adapt(HEALTHY_TO_HYPEROPIC)
        output = study.run()
        assert output[0]["text"] == "Hello World"


class TestBlindProfile:
    def test_adds_speech(self):
        study = HTMLViewerStudy()
        study.run()
        study.adapt(HEALTHY_TO_BLIND)
        output = study.run()
        assert output[0]["profile"] == "blind"
        assert study.speech_buffer == ["Hello World"]

    def test_text_still_printed(self):
        study = HTMLViewerStudy()
        study.adapt(HEALTHY_TO_BLIND)
        output = study.run()
        assert output[0]["text"] == "Hello World"


class TestSystemWide:
    def test_all_prints_change(self):
        """Multiple print statements all change profile simultaneously."""
        study = HTMLViewerStudy()
        study.adapt(HEALTHY_TO_BLIND)
        output = study.run(VIEWER_MULTI_PRINT)
        assert len(output) == 2
        assert all(o["profile"] == "blind" for o in output)
        assert study.speech_buffer == ["First line", "Second line"]

    def test_font_settings_independent(self):
        """set font color/size are unaffected by print adaptation."""
        study = HTMLViewerStudy()
        study.adapt(HEALTHY_TO_HYPEROPIC)
        output = study.run()
        assert output[0]["color"] == "red"  # set font color still works

    def test_program_text_unchanged(self):
        study = HTMLViewerStudy()
        text_before = study.program_text
        study.adapt(HEALTHY_TO_BLIND)
        assert study.program_text == text_before == VIEWER_PROGRAM
