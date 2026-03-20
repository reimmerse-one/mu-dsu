"""CalcLang — imperative language for the Mandelbrot study (Sect. 5.2)."""

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.calc_lang.slices import (
    expr_slice, for_loop_slice, program_slice,
    support_slice, var_decl_slice, while_loop_slice,
)


def compose_calclang() -> tuple[GrammarComposer, ActionRegistry]:
    composer = GrammarComposer()
    actions = ActionRegistry()

    for sl in [
        support_slice(), expr_slice(), var_decl_slice(),
        for_loop_slice(), while_loop_slice(), program_slice(),
    ]:
        composer.register(sl)
        actions.load_from_slice(sl)

    return composer, actions


def create_interpreter() -> Interpreter:
    composer, actions = compose_calclang()
    return Interpreter(composer, actions)
