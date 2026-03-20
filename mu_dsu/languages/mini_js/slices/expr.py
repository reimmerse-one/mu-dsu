"""Expression slice — arithmetic, member access, identifiers, literals."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def expr_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.expr",
        syntax=SyntaxDefinition(
            rules=(
                '?expr: expr "+" mul_expr -> add\n'
                '    | expr "-" mul_expr -> sub\n'
                "    | mul_expr\n"
                '?mul_expr: mul_expr "*" atom -> mul\n'
                "    | atom\n"
                "?atom: member_access\n"
                "    | NUMBER -> number_lit\n"
                "    | STRING -> string_lit\n"
                "    | IDENT -> var_ref\n"
                'member_access: IDENT "." IDENT'
            ),
        ),
        dependencies=["viewer.support"],
        actions=[
            SemanticAction(
                node_type="number_lit", role="execution", phase="replace",
                handler=lambda n, c, v: int(n.children[0]),
                id="viewer.number_lit.exec",
            ),
            SemanticAction(
                node_type="string_lit", role="execution", phase="replace",
                handler=lambda n, c, v: str(n.children[0]).strip('"').strip("'"),
                id="viewer.string_lit.exec",
            ),
            SemanticAction(
                node_type="var_ref", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.get(str(n.children[0])),
                id="viewer.var_ref.exec",
            ),
            SemanticAction(
                node_type="member_access", role="execution", phase="replace",
                handler=_exec_member_access,
                id="viewer.member_access.exec",
            ),
            SemanticAction(
                node_type="add", role="execution", phase="replace",
                handler=lambda n, c, v: v(n.children[0]) + v(n.children[1]),
                id="viewer.add.exec",
            ),
            SemanticAction(
                node_type="sub", role="execution", phase="replace",
                handler=lambda n, c, v: v(n.children[0]) - v(n.children[1]),
                id="viewer.sub.exec",
            ),
            SemanticAction(
                node_type="mul", role="execution", phase="replace",
                handler=lambda n, c, v: v(n.children[0]) * v(n.children[1]),
                id="viewer.mul.exec",
            ),
        ],
    )


def _exec_member_access(node, ctx, visit):
    """obj.attr — lookup obj as a dict in env, return obj[attr]."""
    obj_name = str(node.children[0])
    attr_name = str(node.children[1])
    obj = ctx.env.get(obj_name)
    if isinstance(obj, dict):
        return obj[attr_name]
    return getattr(obj, attr_name, None)
