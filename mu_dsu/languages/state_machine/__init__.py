"""HooverLang — State Machine Language for the vacuum cleaner example.

Based on the language described in Sections 2.3 and 3.2 of the μ-DSU paper.
Composed from 10 slices following the Neverlang slice model.
"""

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.environment import Environment
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.state_machine.runner import StateMachineRunner
from mu_dsu.languages.state_machine.slices import (
    action_slice,
    bool_expr_slice,
    event_decl_slice,
    event_slice,
    expr_slice,
    program_slice,
    state_decl_slice,
    state_slice,
    support_slice,
    transition_slice,
)


def compose_hooverlang() -> tuple[GrammarComposer, ActionRegistry]:
    """Compose all HooverLang slices into a working language."""
    composer = GrammarComposer()
    actions = ActionRegistry()

    all_slices = [
        support_slice(),
        expr_slice(),
        bool_expr_slice(),
        action_slice(),
        state_slice(),
        state_decl_slice(),
        event_slice(),
        event_decl_slice(),
        transition_slice(),
        program_slice(),
    ]

    for sl in all_slices:
        composer.register(sl)
        actions.load_from_slice(sl)

    return composer, actions


def create_runner() -> StateMachineRunner:
    """Create a ready-to-use HooverLang state machine runner."""
    composer, actions = compose_hooverlang()
    interp = Interpreter(composer, actions)
    return StateMachineRunner(interp)


__all__ = ["compose_hooverlang", "create_runner", "StateMachineRunner"]
