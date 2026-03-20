"""State slices — state definitions and the states section."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def state_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.state",
        syntax=SyntaxDefinition(
            rules='state_def: IDENT "=" action_list',
        ),
        dependencies=["sm.action"],
        actions=[
            SemanticAction(
                node_type="state_def", role="execution", phase="replace",
                handler=_exec_state_def,
                id="sm.state_def.exec",
            ),
        ],
    )


def state_decl_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.state_decl",
        syntax=SyntaxDefinition(
            rules='states_section: "states" state_def+',
        ),
        dependencies=["sm.state"],
        actions=[
            SemanticAction(
                node_type="states_section", role="execution", phase="replace",
                handler=_exec_states_section,
                id="sm.states_section.exec",
            ),
        ],
    )


def _exec_state_def(node, ctx, visit):
    """Register a state: store name and action_list AST node for re-execution."""
    name = str(node.children[0])
    action_list_node = node.children[1]
    states = ctx.env.get("__sm_states__")
    states[name] = action_list_node
    return name


def _exec_states_section(node, ctx, visit):
    """Process all state definitions."""
    if not ctx.env.has("__sm_states__"):
        ctx.env.set("__sm_states__", {})
    for child in node.children:
        visit(child)
