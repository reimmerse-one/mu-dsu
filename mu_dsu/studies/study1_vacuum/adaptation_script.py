"""μDA adaptation script for the vacuum cleaner stand-by study (Sect. 3.2)."""

STANDBY_ADAPTATION = """\
// Seamless adaptation: add stand-by awareness to turn-on semantics
context {
    slice old: sm.state;
    slice new: sm.state_standby;
}
system-wide {
    replace slice old with new;
    redo role execution;
}
"""
