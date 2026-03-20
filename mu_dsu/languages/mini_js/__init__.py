"""MiniJS — simplified JavaScript for the HTML viewer study (Sect. 5.1)."""

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.mini_js.slices import (
    expr_slice, print_healthy_slice, program_slice,
    set_font_slice, support_slice, var_decl_slice,
)


def compose_mini_js() -> tuple[GrammarComposer, ActionRegistry]:
    """Compose MiniJS with the default HealthyPrint profile."""
    composer = GrammarComposer()
    actions = ActionRegistry()

    for sl in [
        support_slice(), expr_slice(), var_decl_slice(),
        set_font_slice(), print_healthy_slice(), program_slice(),
    ]:
        composer.register(sl)
        actions.load_from_slice(sl)

    return composer, actions


def create_interpreter() -> Interpreter:
    composer, actions = compose_mini_js()
    return Interpreter(composer, actions)
