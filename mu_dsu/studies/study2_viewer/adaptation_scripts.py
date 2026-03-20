"""μDA adaptation scripts for the HTML viewer study (Sect. 5.1)."""

HEALTHY_TO_BLIND = """\
context {
    slice old: viewer.print;
    slice new: viewer.print_blind;
}
system-wide {
    replace slice old with new;
    redo role execution;
}
"""

HEALTHY_TO_HYPEROPIC = """\
context {
    slice old: viewer.print;
    slice new: viewer.print_hyperopic;
}
system-wide {
    replace slice old with new;
    redo role execution;
}
"""
