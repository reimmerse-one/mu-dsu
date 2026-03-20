"""Expression slice — arithmetic, comparison, logical, array access."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def expr_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.expr",
        syntax=SyntaxDefinition(
            rules=(
                '?expr: expr "&&" comp_expr -> logic_and\n'
                "    | comp_expr\n"
                '?comp_expr: comp_expr ">" arith_expr -> gt\n'
                '    | comp_expr "<" arith_expr -> lt\n'
                '    | comp_expr ">=" arith_expr -> gte\n'
                '    | comp_expr "<=" arith_expr -> lte\n'
                "    | arith_expr\n"
                '?arith_expr: arith_expr "+" term -> add\n'
                '    | arith_expr "-" term -> sub\n'
                "    | term\n"
                '?term: term "*" factor -> mul\n'
                '    | term "/" factor -> div\n'
                "    | factor\n"
                '?factor: "(" expr ")"\n'
                "    | array_access\n"
                "    | DECIMAL -> float_lit\n"
                "    | NUMBER -> number_lit\n"
                "    | IDENT -> var_ref\n"
                'array_access: IDENT "[" expr "]" "[" expr "]"'
            ),
        ),
        dependencies=["calc.support"],
        actions=[
            SemanticAction(node_type="number_lit", role="execution", phase="replace",
                           handler=lambda n, c, v: int(n.children[0]), id="calc.number.exec"),
            SemanticAction(node_type="float_lit", role="execution", phase="replace",
                           handler=lambda n, c, v: float(n.children[0]), id="calc.float.exec"),
            SemanticAction(node_type="var_ref", role="execution", phase="replace",
                           handler=lambda n, c, v: c.env.get(str(n.children[0])), id="calc.var_ref.exec"),
            SemanticAction(node_type="add", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) + v(n.children[1]), id="calc.add.exec"),
            SemanticAction(node_type="sub", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) - v(n.children[1]), id="calc.sub.exec"),
            SemanticAction(node_type="mul", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) * v(n.children[1]), id="calc.mul.exec"),
            SemanticAction(node_type="div", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) / v(n.children[1]), id="calc.div.exec"),
            SemanticAction(node_type="gt", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) > v(n.children[1]), id="calc.gt.exec"),
            SemanticAction(node_type="lt", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) < v(n.children[1]), id="calc.lt.exec"),
            SemanticAction(node_type="gte", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) >= v(n.children[1]), id="calc.gte.exec"),
            SemanticAction(node_type="lte", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) <= v(n.children[1]), id="calc.lte.exec"),
            SemanticAction(node_type="logic_and", role="execution", phase="replace",
                           handler=lambda n, c, v: v(n.children[0]) and v(n.children[1]), id="calc.and.exec"),
            SemanticAction(node_type="array_access", role="execution", phase="replace",
                           handler=_exec_array_access, id="calc.array_access.exec"),
        ],
    )


def _exec_array_access(node, ctx, visit):
    """arr[i][j] — 2D array access."""
    name = str(node.children[0])
    i = visit(node.children[1])
    j = visit(node.children[2])
    arr = ctx.env.get(name)
    return arr[int(i)][int(j)]
