"""HealthyPrint slice (Listing 5a) — default print, no accessibility."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def print_healthy_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.print",
        syntax=SyntaxDefinition(
            rules='print_stmt: "print" expr ";"',
        ),
        dependencies=["viewer.expr"],
        actions=[
            SemanticAction(
                node_type="print_stmt", role="execution", phase="replace",
                handler=_exec_print_healthy,
                id="viewer.print_stmt.exec",
            ),
        ],
    )


def _exec_print_healthy(node, ctx, visit):
    """Normal print: output text at current font settings."""
    text = visit(node.children[0])
    size = ctx.env.get("__font_size__") if ctx.env.has("__font_size__") else 12
    color = ctx.env.get("__font_color__") if ctx.env.has("__font_color__") else "black"
    output = ctx.env.get("__output__") if ctx.env.has("__output__") else []
    output.append({"text": str(text), "size": size, "color": color, "profile": "healthy"})
    ctx.env.set("__output__", output)
    return text
