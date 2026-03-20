"""Study 2: HTML Viewer Accessibility Adaptation (Sect. 5.1).

Demonstrates system-wide adaptation — all print statements change
simultaneously when the user profile changes.
"""

from __future__ import annotations

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.mini_js import compose_mini_js
from mu_dsu.languages.mini_js.slices.print_blind import print_blind_slice
from mu_dsu.languages.mini_js.slices.print_healthy import print_healthy_slice
from mu_dsu.languages.mini_js.slices.print_hyperopic import print_hyperopic_slice
from mu_dsu.studies.study2_viewer.programs import VIEWER_PROGRAM


class HTMLViewerStudy:
    """Orchestrates the HTML viewer accessibility study."""

    def __init__(self) -> None:
        composer, actions = compose_mini_js()
        self.interpreter = Interpreter(composer, actions)
        self.adapter = MicroLanguageAdapter(slice_registry={
            "viewer.print_blind": print_blind_slice(),
            "viewer.print_hyperopic": print_hyperopic_slice(),
            "viewer.print_healthy": print_healthy_slice(),
        })
        self.program_text = VIEWER_PROGRAM

    def run(self, program: str | None = None) -> list[dict]:
        """Run program and return output entries."""
        self.interpreter.env.set("__output__", [])
        if self.interpreter.env.has("__speech__"):
            self.interpreter.env.set("__speech__", [])
        self.interpreter.run(program or self.program_text)
        return self.interpreter.env.get("__output__")

    def adapt(self, script: str) -> bool:
        result = self.adapter.adapt(script, self.interpreter)
        return result.success

    @property
    def speech_buffer(self) -> list[str]:
        if self.interpreter.env.has("__speech__"):
            return self.interpreter.env.get("__speech__")
        return []
