"""MiniJS slice factory functions."""

from mu_dsu.languages.mini_js.slices.support import support_slice
from mu_dsu.languages.mini_js.slices.expr import expr_slice
from mu_dsu.languages.mini_js.slices.var_decl import var_decl_slice
from mu_dsu.languages.mini_js.slices.set_font import set_font_slice
from mu_dsu.languages.mini_js.slices.print_healthy import print_healthy_slice
from mu_dsu.languages.mini_js.slices.print_hyperopic import print_hyperopic_slice
from mu_dsu.languages.mini_js.slices.print_blind import print_blind_slice
from mu_dsu.languages.mini_js.slices.program import program_slice

__all__ = [
    "support_slice", "expr_slice", "var_decl_slice", "set_font_slice",
    "print_healthy_slice", "print_hyperopic_slice", "print_blind_slice",
    "program_slice",
]
