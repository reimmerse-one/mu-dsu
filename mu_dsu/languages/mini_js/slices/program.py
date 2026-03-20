"""Program slice — top-level MiniJS structure."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def program_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.program",
        syntax=SyntaxDefinition(
            rules=(
                "start: statement+\n"
                "?statement: var_stmt\n"
                "    | print_stmt\n"
                "    | set_font_size\n"
                "    | set_font_color"
            ),
        ),
        dependencies=["viewer.var_decl", "viewer.print", "viewer.set_font"],
        actions=[
            SemanticAction(
                node_type="start", role="execution", phase="replace",
                handler=lambda n, c, v: [v(child) for child in n.children],
                id="viewer.program.exec",
            ),
        ],
    )
