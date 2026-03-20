"""HooverLang slice factory functions."""

from mu_dsu.languages.state_machine.slices.support import support_slice
from mu_dsu.languages.state_machine.slices.expr import expr_slice
from mu_dsu.languages.state_machine.slices.bool_expr import bool_expr_slice
from mu_dsu.languages.state_machine.slices.action import action_slice
from mu_dsu.languages.state_machine.slices.state import state_slice, state_decl_slice
from mu_dsu.languages.state_machine.slices.event import event_slice, event_decl_slice
from mu_dsu.languages.state_machine.slices.transition import transition_slice
from mu_dsu.languages.state_machine.slices.program import program_slice

__all__ = [
    "support_slice",
    "expr_slice",
    "bool_expr_slice",
    "action_slice",
    "state_slice",
    "state_decl_slice",
    "event_slice",
    "event_decl_slice",
    "transition_slice",
    "program_slice",
]
