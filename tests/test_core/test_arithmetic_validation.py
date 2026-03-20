"""Phase 1 validation: arithmetic language from 3 slices.

Build a complete arithmetic language by composing three slices:
1. Numbers (literals + parentheses)
2. Multiplication (* and /)
3. Addition (+ and -)

Validates:
- Grammar composition from multiple slices
- Operator precedence (mul binds tighter than add)
- Semantic action dispatch
- Dynamic action swap (change * semantics at runtime)
- Slice replacement (swap entire multiplication slice)
"""

from lark import Tree

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


# --- Slice definitions ---

def numbers_slice() -> LanguageSlice:
    return LanguageSlice(
        name="arithmetic.numbers",
        syntax=SyntaxDefinition(
            rules='?atom: NUMBER -> number\n    | "(" expr ")"',
            terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
        ),
        actions=[
            SemanticAction(
                node_type="number",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: int(node.children[0]),
                id="number.exec",
            ),
        ],
    )


def multiplication_slice() -> LanguageSlice:
    return LanguageSlice(
        name="arithmetic.multiplication",
        syntax=SyntaxDefinition(
            rules=(
                '?mul_expr: atom\n'
                '    | mul_expr "*" atom -> mul\n'
                '    | mul_expr "/" atom -> div'
            ),
        ),
        dependencies=["arithmetic.numbers"],
        actions=[
            SemanticAction(
                node_type="mul",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) * visit(node.children[1]),
                id="mul.exec",
            ),
            SemanticAction(
                node_type="div",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) / visit(node.children[1]),
                id="div.exec",
            ),
        ],
    )


def addition_slice() -> LanguageSlice:
    return LanguageSlice(
        name="arithmetic.addition",
        syntax=SyntaxDefinition(
            rules=(
                'start: expr\n'
                '?expr: mul_expr\n'
                '    | expr "+" mul_expr -> add\n'
                '    | expr "-" mul_expr -> sub'
            ),
        ),
        dependencies=["arithmetic.multiplication"],
        actions=[
            SemanticAction(
                node_type="add",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) + visit(node.children[1]),
                id="add.exec",
            ),
            SemanticAction(
                node_type="sub",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: visit(node.children[0]) - visit(node.children[1]),
                id="sub.exec",
            ),
        ],
    )


def _build_interpreter() -> Interpreter:
    """Build a full arithmetic interpreter from 3 slices."""
    composer = GrammarComposer()
    actions = ActionRegistry()

    for sl in [numbers_slice(), multiplication_slice(), addition_slice()]:
        composer.register(sl)
        actions.load_from_slice(sl)

    return Interpreter(composer, actions)


# --- Tests ---

class TestArithmeticLanguage:
    """Core validation: 3 slices compose into a working arithmetic language."""

    def test_simple_addition(self):
        interp = _build_interpreter()
        assert interp.run("2 + 3") == 5

    def test_simple_multiplication(self):
        interp = _build_interpreter()
        assert interp.run("3 * 4") == 12

    def test_precedence_mul_before_add(self):
        """2 + 3 * 4 = 2 + 12 = 14 (not (2+3)*4 = 20)."""
        interp = _build_interpreter()
        assert interp.run("2 + 3 * 4") == 14

    def test_parentheses_override_precedence(self):
        """(2 + 3) * 4 = 20."""
        interp = _build_interpreter()
        assert interp.run("(2 + 3) * 4") == 20

    def test_subtraction_with_precedence(self):
        """10 - 2 * 3 = 10 - 6 = 4."""
        interp = _build_interpreter()
        assert interp.run("10 - 2 * 3") == 4

    def test_division(self):
        interp = _build_interpreter()
        assert interp.run("12 / 3") == 4.0

    def test_complex_expression(self):
        interp = _build_interpreter()
        assert interp.run("(1 + 2) * (3 + 4)") == 21

    def test_single_number(self):
        interp = _build_interpreter()
        assert interp.run("42") == 42


class TestDynamicActionSwap:
    """μ-DSU core: swap semantic actions at runtime without reparsing."""

    def test_swap_mul_to_add(self):
        """Replace * semantics with + semantics.

        2 + 3 * 4 -> 2 + (3 + 4) = 9
        """
        interp = _build_interpreter()

        # Verify original behavior
        assert interp.run("2 + 3 * 4") == 14

        # Swap: * now means +
        new_mul_action = SemanticAction(
            node_type="mul",
            role="execution",
            phase="replace",
            handler=lambda node, ctx, visit: visit(node.children[0]) + visit(node.children[1]),
            id="mul.exec.swapped",
        )
        interp.actions.replace_action("mul", "execution", "mul.exec", new_mul_action)

        # Re-run same expression — no reparsing needed
        assert interp.run("2 + 3 * 4") == 9


class TestSliceReplacement:
    """μ-DSU: replace entire language slices at runtime."""

    def test_replace_mul_with_power(self):
        """Replace multiplication slice so * means ** (power).

        2 + 3 * 4 -> 2 + 3**4 = 2 + 81 = 83
        """
        interp = _build_interpreter()
        assert interp.run("2 + 3 * 4") == 14

        # Create a power slice
        power_slice = LanguageSlice(
            name="arithmetic.multiplication",
            syntax=SyntaxDefinition(
                rules=(
                    '?mul_expr: atom\n'
                    '    | mul_expr "*" atom -> mul\n'
                    '    | mul_expr "/" atom -> div'
                ),
            ),
            dependencies=["arithmetic.numbers"],
            actions=[
                SemanticAction(
                    node_type="mul",
                    role="execution",
                    phase="replace",
                    handler=lambda node, ctx, visit: visit(node.children[0]) ** visit(node.children[1]),
                    id="mul.exec",
                ),
                SemanticAction(
                    node_type="div",
                    role="execution",
                    phase="replace",
                    handler=lambda node, ctx, visit: visit(node.children[0]) / visit(node.children[1]),
                    id="div.exec",
                ),
            ],
        )

        # Unload old actions, replace slice, load new actions
        old_mul = multiplication_slice()
        interp.actions.unload_slice(old_mul)
        interp.composer.replace("arithmetic.multiplication", power_slice)
        interp.actions.load_from_slice(power_slice)
        interp.invalidate_parser()

        # 2 + 3**4 = 2 + 81 = 83
        assert interp.run("2 + 3 * 4") == 83
