"""Program slice — top-level CalcLang structure."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def program_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.program",
        syntax=SyntaxDefinition(
            rules=(
                "start: statement+\n"
                "?statement: var_stmt\n"
                "    | assign_stmt\n"
                "    | array_assign\n"
                "    | for_stmt\n"
                "    | while_stmt\n"
                '    | expr ";" -> expr_stmt'
            ),
        ),
        dependencies=["calc.var_decl", "calc.for_loop", "calc.while_loop"],
        actions=[
            SemanticAction(
                node_type="start", role="execution", phase="replace",
                handler=lambda n, c, v: [v(ch) for ch in n.children],
                id="calc.program.exec",
            ),
            SemanticAction(
                node_type="expr_stmt", role="execution", phase="replace",
                handler=lambda n, c, v: v(n.children[0]),
                id="calc.expr_stmt.exec",
            ),
        ],
    )
