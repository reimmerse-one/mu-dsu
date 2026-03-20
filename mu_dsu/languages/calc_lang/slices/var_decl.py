"""Variable declaration and assignment slices for CalcLang."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def var_decl_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.var_decl",
        syntax=SyntaxDefinition(
            rules=(
                'var_stmt: "var" IDENT "=" expr ";"\n'
                'assign_stmt: IDENT "=" expr ";"\n'
                'array_assign: IDENT "[" expr "]" "[" expr "]" "=" expr ";"'
            ),
        ),
        dependencies=["calc.expr"],
        actions=[
            SemanticAction(
                node_type="var_stmt", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="calc.var_stmt.exec",
            ),
            SemanticAction(
                node_type="assign_stmt", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="calc.assign_stmt.exec",
            ),
            SemanticAction(
                node_type="array_assign", role="execution", phase="replace",
                handler=_exec_array_assign,
                id="calc.array_assign.exec",
            ),
        ],
    )


def _exec_array_assign(node, ctx, visit):
    """arr[i][j] = expr;"""
    name = str(node.children[0])
    i = int(visit(node.children[1]))
    j = int(visit(node.children[2]))
    val = visit(node.children[3])
    arr = ctx.env.get(name)
    arr[i][j] = val
