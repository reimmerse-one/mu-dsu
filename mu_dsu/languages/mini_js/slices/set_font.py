"""Set font size/color slices (Table 2 from the paper)."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def set_font_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.set_font",
        syntax=SyntaxDefinition(
            rules=(
                'set_font_size: "set" "font" "size" expr ";"\n'
                'set_font_color: "set" "font" "color" expr ";"'
            ),
        ),
        dependencies=["viewer.expr"],
        actions=[
            SemanticAction(
                node_type="set_font_size", role="execution", phase="replace",
                handler=_exec_set_font_size,
                id="viewer.set_font_size.exec",
            ),
            SemanticAction(
                node_type="set_font_color", role="execution", phase="replace",
                handler=_exec_set_font_color,
                id="viewer.set_font_color.exec",
            ),
        ],
    )


def _exec_set_font_size(node, ctx, visit):
    size = visit(node.children[0])
    ctx.env.set("__font_size__", size)
    return size


def _exec_set_font_color(node, ctx, visit):
    color = visit(node.children[0])
    ctx.env.set("__font_color__", color)
    return color
