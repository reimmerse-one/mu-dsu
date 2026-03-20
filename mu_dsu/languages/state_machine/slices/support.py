"""Support slice — terminals (IDENT, NUMBER) and counter declarations."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def support_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.support",
        syntax=SyntaxDefinition(
            rules='counter_decl: "counter" IDENT',
            terminals=(
                # IDENT allows hyphens between alphabetic segments (turn-on, stand-by)
                # but NOT at the end, so `t - 1` parses as IDENT MINUS NUMBER
                "IDENT: /[a-zA-Z_][a-zA-Z0-9_]*(-[a-zA-Z_][a-zA-Z0-9_]*)*/\n"
                "%import common.NUMBER\n"
                "%import common.WS\n"
                "%ignore WS\n"
                "%ignore /\\n/\n"
            ),
        ),
        actions=[
            SemanticAction(
                node_type="counter_decl",
                role="execution",
                phase="replace",
                handler=_exec_counter_decl,
                id="counter_decl.exec",
            ),
        ],
    )


def _exec_counter_decl(node, ctx, visit):
    """Declare a counter variable, initialized to 0."""
    name = str(node.children[0])
    ctx.env.set(name, 0)
    return name
