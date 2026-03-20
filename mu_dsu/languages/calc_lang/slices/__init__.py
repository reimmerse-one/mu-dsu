"""CalcLang slice factory functions."""

from mu_dsu.languages.calc_lang.slices.support import support_slice
from mu_dsu.languages.calc_lang.slices.expr import expr_slice
from mu_dsu.languages.calc_lang.slices.var_decl import var_decl_slice
from mu_dsu.languages.calc_lang.slices.for_loop import for_loop_slice
from mu_dsu.languages.calc_lang.slices.par_for_loop import par_for_loop_slice
from mu_dsu.languages.calc_lang.slices.while_loop import while_loop_slice
from mu_dsu.languages.calc_lang.slices.program import program_slice

__all__ = [
    "support_slice", "expr_slice", "var_decl_slice",
    "for_loop_slice", "par_for_loop_slice", "while_loop_slice",
    "program_slice",
]
