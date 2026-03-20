"""Event slices — event definitions and the events section."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def event_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.event",
        syntax=SyntaxDefinition(
            rules=(
                'event_def: IDENT "=" event_expr\n'
                "?event_expr: func_call\n"
                "    | bool_expr"
            ),
        ),
        dependencies=["sm.bool_expr", "sm.action"],
        actions=[
            SemanticAction(
                node_type="event_def", role="execution", phase="replace",
                handler=_exec_event_def,
                id="sm.event_def.exec",
            ),
        ],
    )


def event_decl_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.event_decl",
        syntax=SyntaxDefinition(
            rules='events_section: "events" event_def+',
        ),
        dependencies=["sm.event"],
        actions=[
            SemanticAction(
                node_type="events_section", role="execution", phase="replace",
                handler=_exec_events_section,
                id="sm.events_section.exec",
            ),
        ],
    )


def _exec_event_def(node, ctx, visit):
    """Register an event: store name and condition AST node for re-evaluation."""
    name = str(node.children[0])
    condition_node = node.children[1]
    events = ctx.env.get("__sm_events__")
    events[name] = condition_node
    return name


def _exec_events_section(node, ctx, visit):
    """Process all event definitions."""
    if not ctx.env.has("__sm_events__"):
        ctx.env.set("__sm_events__", {})
    for child in node.children:
        visit(child)
