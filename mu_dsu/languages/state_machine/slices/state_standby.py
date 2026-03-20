"""Stand-by variant of the state slice.

Modified semantics: entering the "on" state also resets counter t to 0.
Used to demonstrate system-wide μDA adaptation (Section 3.2 of the paper).
"""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def state_standby_slice() -> LanguageSlice:
    """Replacement state slice with counter-reset on 'on' entry."""
    return LanguageSlice(
        name="sm.state",
        syntax=SyntaxDefinition(
            rules='state_def: IDENT "=" action_list',
        ),
        dependencies=["sm.action"],
        actions=[
            SemanticAction(
                node_type="state_def", role="execution", phase="replace",
                handler=_exec_state_def_standby,
                id="sm.state_def.exec",
            ),
        ],
    )


def _exec_state_def_standby(node, ctx, visit):
    """Register a state + reset counter t when entering 'on'."""
    name = str(node.children[0])
    action_list_node = node.children[1]
    states = ctx.env.get("__sm_states__")
    states[name] = action_list_node

    # Stand-by extension: mark that standby-aware semantics are active
    if name == "on":
        ctx.env.set("__sm_standby_enabled__", True)
    return name
