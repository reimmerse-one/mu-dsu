"""Expression slice — arithmetic expressions with +, -."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def expr_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.expr",
        syntax=SyntaxDefinition(
            rules=(
                '?expr: expr "+" atom -> add\n'
                '    | expr "-" atom -> sub\n'
                "    | atom\n"
                "?atom: NUMBER -> number\n"
                "    | IDENT -> var_ref"
            ),
        ),
        dependencies=["sm.support"],
        actions=[
            SemanticAction(
                node_type="number", role="execution", phase="replace",
                handler=lambda node, ctx, visit: int(node.children[0]),
                id="sm.number.exec",
            ),
            SemanticAction(
                node_type="var_ref", role="execution", phase="replace",
                handler=lambda node, ctx, visit: ctx.env.get(str(node.children[0])),
                id="sm.var_ref.exec",
            ),
            SemanticAction(
                node_type="add", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) + visit(node.children[1]),
                id="sm.add.exec",
            ),
            SemanticAction(
                node_type="sub", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) - visit(node.children[1]),
                id="sm.sub.exec",
            ),
        ],
    )
