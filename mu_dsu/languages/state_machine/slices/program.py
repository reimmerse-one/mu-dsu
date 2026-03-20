"""Program slice — top-level structure of a HooverLang program."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def program_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.program",
        syntax=SyntaxDefinition(
            rules=(
                "start: section+\n"
                "?section: counter_decl\n"
                "    | states_section\n"
                "    | events_section\n"
                "    | transitions_section"
            ),
        ),
        dependencies=["sm.state_decl", "sm.event_decl", "sm.transition"],
        actions=[
            SemanticAction(
                node_type="start", role="execution", phase="replace",
                handler=_exec_program,
                id="sm.program.exec",
            ),
        ],
    )


def _exec_program(node, ctx, visit):
    """Execute all sections — populates state/event/transition tables in env."""
    # Reset SM data structures (clean slate for redo)
    ctx.env.set("__sm_states__", {})
    ctx.env.set("__sm_events__", {})
    ctx.env.set("__sm_transitions__", {})

    for child in node.children:
        visit(child)

    return {
        "states": ctx.env.get("__sm_states__"),
        "events": ctx.env.get("__sm_events__"),
        "transitions": ctx.env.get("__sm_transitions__"),
    }
