"""While loop slice."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def while_loop_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.while_loop",
        syntax=SyntaxDefinition(
            rules='while_stmt: "while" "(" expr ")" "{" statement_list "}" ";"',
        ),
        dependencies=["calc.for_loop"],
        actions=[
            SemanticAction(
                node_type="while_stmt", role="execution", phase="replace",
                handler=_exec_while, id="calc.while_stmt.exec",
            ),
        ],
    )


def _exec_while(node, ctx, visit):
    cond_node = node.children[0]
    body_node = node.children[1]
    iterations = 0
    max_iter = 100000
    while visit(cond_node) and iterations < max_iter:
        visit(body_node)
        iterations += 1
