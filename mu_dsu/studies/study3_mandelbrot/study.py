"""Study 3: Mandelbrot Localised Adaptation (Sect. 5.2).

Demonstrates localised adaptation — only the inner for loop
is parallelised, the outer for remains sequential.
"""

from __future__ import annotations

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.calc_lang import compose_calclang
from mu_dsu.languages.calc_lang.slices.par_for_loop import par_for_loop_slice
from mu_dsu.studies.study3_mandelbrot.adaptation_scripts import (
    FOR_TO_PARFOR_LOCALISED,
    FOR_TO_PARFOR_SYSTEM_WIDE,
)


class MandelbrotStudy:
    """Orchestrates the Mandelbrot for->parfor adaptation study."""

    def __init__(self) -> None:
        composer, actions = compose_calclang()
        self.interpreter = Interpreter(composer, actions)
        self.adapter = MicroLanguageAdapter(slice_registry={
            "calc.par_for_loop": par_for_loop_slice(),
        })

    def run(self, program: str | None = None) -> None:
        """Parse and run a CalcLang program.

        If program is None, re-execute the current parse tree without reparsing.
        This is essential after localised adaptation, which installs dispatchers
        on specific parse tree nodes — reparsing would create new nodes.
        """
        self.interpreter.env.set("__exec_modes__", [])
        if program is not None:
            self.interpreter.run(program)
        else:
            self.interpreter.run()  # reuse existing parse tree

    def adapt_localised(self) -> bool:
        """Apply localised adaptation: only inner for → parfor."""
        result = self.adapter.adapt(FOR_TO_PARFOR_LOCALISED, self.interpreter)
        return result.success

    def adapt_system_wide(self) -> bool:
        """Apply system-wide adaptation: ALL for → parfor."""
        result = self.adapter.adapt(FOR_TO_PARFOR_SYSTEM_WIDE, self.interpreter)
        return result.success

    @property
    def execution_modes(self) -> list[str]:
        if self.interpreter.env.has("__exec_modes__"):
            return self.interpreter.env.get("__exec_modes__")
        return []
