"""BlindPrint slice (Listing 5c) — text-to-speech for blind users."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def print_blind_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.print",
        syntax=SyntaxDefinition(
            rules='print_stmt: "print" expr ";"',
        ),
        dependencies=["viewer.expr"],
        actions=[
            SemanticAction(
                node_type="print_stmt", role="execution", phase="replace",
                handler=_exec_print_blind,
                id="viewer.print_stmt.exec",
            ),
        ],
    )


def _exec_print_blind(node, ctx, visit):
    """Blind print: output text AND speak it."""
    text = visit(node.children[0])
    size = ctx.env.get("__font_size__") if ctx.env.has("__font_size__") else 12
    color = ctx.env.get("__font_color__") if ctx.env.has("__font_color__") else "black"
    output = ctx.env.get("__output__") if ctx.env.has("__output__") else []
    output.append({"text": str(text), "size": size, "color": color, "profile": "blind"})
    ctx.env.set("__output__", output)
    # Text-to-speech
    speech = ctx.env.get("__speech__") if ctx.env.has("__speech__") else []
    speech.append(str(text))
    ctx.env.set("__speech__", speech)
    return text
