"""Transition slice — transition definitions with => arrows."""

from lark import Token

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def transition_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.transition",
        syntax=SyntaxDefinition(
            rules=(
                'transitions_section: "transitions" trans_def+\n'
                'trans_def: IDENT "{" trans_rule (";" trans_rule)* "}"\n'
                'trans_rule: IDENT "=>" IDENT'
            ),
        ),
        dependencies=["sm.support"],
        actions=[
            SemanticAction(
                node_type="transitions_section", role="execution", phase="replace",
                handler=_exec_transitions_section,
                id="sm.transitions_section.exec",
            ),
            SemanticAction(
                node_type="trans_def", role="execution", phase="replace",
                handler=_exec_trans_def,
                id="sm.trans_def.exec",
            ),
            SemanticAction(
                node_type="trans_rule", role="execution", phase="replace",
                handler=_exec_trans_rule,
                id="sm.trans_rule.exec",
            ),
        ],
    )


def _exec_transitions_section(node, ctx, visit):
    """Process all transition definitions."""
    if not ctx.env.has("__sm_transitions__"):
        ctx.env.set("__sm_transitions__", {})
    for child in node.children:
        visit(child)


def _exec_trans_def(node, ctx, visit):
    """Register transitions for a state."""
    state_name = str(node.children[0])
    transitions = ctx.env.get("__sm_transitions__")
    if state_name not in transitions:
        transitions[state_name] = []
    for child in node.children[1:]:
        if not isinstance(child, Token):  # Skip punctuation tokens
            rule = visit(child)
            if rule is not None:
                transitions[state_name].append(rule)
    return state_name


def _exec_trans_rule(node, ctx, visit):
    """Return (event_name, target_state) tuple."""
    event_name = str(node.children[0])
    target_state = str(node.children[1])
    return (event_name, target_state)
