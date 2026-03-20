"""μDA adaptation scripts for Mandelbrot parallelisation (Sect. 5.2, Listing 8)."""

# Localised: only the inner for becomes parallel
FOR_TO_PARFOR_LOCALISED = """\
context {
    nt for1, for2 : for_stmt from module calc.for_loop;
    action parforAct : for_stmt from module calc.par_for_loop role execution;
}
when for1 << for2 | for2 occurs {
    set specialized action for for2 to parforAct in role execution;
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
