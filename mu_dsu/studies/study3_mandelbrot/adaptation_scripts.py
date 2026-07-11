"""μDA adaptation scripts for Mandelbrot parallelisation (Sect. 5.2, Listing 8)."""

# Localised: only the inner for becomes parallel.
# Mirrors Listing 8(a) — bare context definitions, placeholders for the
# unused nonterminals, and Table 1's argument order for set specialized.
FOR_TO_PARFOR_LOCALISED = """\
nt for1,_,_,_ : for_stmt from module calc.for_loop;
nt for2,_,_,_ : for_stmt from module calc.for_loop;
action parforAct : for_stmt from module calc.par_for_loop role execution;
when for1 << for2 | for2 occurs {
    set specialized action parforAct to for2 in role execution;
}
"""

# System-wide (for comparison): ALL for loops become parallel
FOR_TO_PARFOR_SYSTEM_WIDE = """\
context {
    slice old: calc.for_loop;
    slice new: calc.par_for_loop;
}
system-wide {
    replace slice old with new;
    redo role execution;
}
"""
