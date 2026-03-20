"""Boolean expression slice — comparisons for event conditions."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def bool_expr_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.bool_expr",
        syntax=SyntaxDefinition(
            rules=(
                'bool_expr: expr ">" expr -> gt\n'
                '    | expr "<" expr -> lt\n'
                '    | expr ">=" expr -> gte\n'
                '    | expr "<=" expr -> lte'
            ),
        ),
        dependencies=["sm.expr"],
        actions=[
            SemanticAction(
                node_type="gt", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) > visit(node.children[1]),
                id="sm.gt.exec",
            ),
            SemanticAction(
                node_type="lt", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) < visit(node.children[1]),
                id="sm.lt.exec",
            ),
            SemanticAction(
                node_type="gte", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) >= visit(node.children[1]),
                id="sm.gte.exec",
            ),
            SemanticAction(
                node_type="lte", role="execution", phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) <= visit(node.children[1]),
                id="sm.lte.exec",
            ),
        ],
    )
