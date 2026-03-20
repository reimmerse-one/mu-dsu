"""Variable declaration slice."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def var_decl_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.var_decl",
        syntax=SyntaxDefinition(
            rules='var_stmt: "var" IDENT "=" expr ";"',
        ),
        dependencies=["viewer.expr"],
        actions=[
            SemanticAction(
                node_type="var_stmt", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="viewer.var_stmt.exec",
            ),
        ],
    )
