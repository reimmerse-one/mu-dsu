"""HyperopicPrint slice (Listing 5b) — enlarged font for long-sighted users."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def print_hyperopic_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.print",
        syntax=SyntaxDefinition(
            rules='print_stmt: "print" expr ";"',
        ),
        dependencies=["viewer.expr"],
        actions=[
            SemanticAction(
                node_type="print_stmt", role="execution", phase="replace",
                handler=_exec_print_hyperopic,
                id="viewer.print_stmt.exec",
            ),
        ],
    )


def _exec_print_hyperopic(node, ctx, visit):
    """Hyperopic print: multiply font size by 3."""
    text = visit(node.children[0])
    size = ctx.env.get("__font_size__") if ctx.env.has("__font_size__") else 12
    color = ctx.env.get("__font_color__") if ctx.env.has("__font_color__") else "black"
    enlarged_size = size * 3
    output = ctx.env.get("__output__") if ctx.env.has("__output__") else []
    output.append({"text": str(text), "size": enlarged_size, "color": color, "profile": "hyperopic"})
    ctx.env.set("__output__", output)
    return text
