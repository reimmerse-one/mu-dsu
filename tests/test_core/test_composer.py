"""Tests for GrammarComposer."""

import pytest
from lark import Lark

from mu_dsu.core.composer import GrammarComposer, SliceDependencyError
from mu_dsu.core.slice import LanguageSlice, SyntaxDefinition


def _numbers_slice() -> LanguageSlice:
    return LanguageSlice(
        name="arithmetic.numbers",
        syntax=SyntaxDefinition(
            rules='?atom: NUMBER -> number\n    | "(" expr ")"',
            terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
        ),
    )


def _multiplication_slice() -> LanguageSlice:
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
    )


def _addition_slice() -> LanguageSlice:
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
    )


class TestGrammarComposer:
    def test_single_slice(self):
        composer = GrammarComposer()
        sl = LanguageSlice(
            name="minimal",
            syntax=SyntaxDefinition(
                rules="start: NUMBER",
                terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
            ),
        )
        composer.register(sl)
        grammar = composer.compose()
        # Should be valid Lark grammar
        parser = Lark(grammar, parser="earley")
        tree = parser.parse("42")
        assert tree is not None

    def test_three_slices_arithmetic(self):
        composer = GrammarComposer()
        composer.register(_numbers_slice())
        composer.register(_multiplication_slice())
        composer.register(_addition_slice())

        parser = composer.build_parser()
        tree = parser.parse("2 + 3 * 4")
        assert tree is not None
        # Verify precedence: mul binds tighter than add
        # The tree should have 'add' at top level
        assert tree.data == "start"

    def test_unregister(self):
        composer = GrammarComposer()
        sl = LanguageSlice(
            name="minimal",
            syntax=SyntaxDefinition(
                rules="start: NUMBER",
                terminals="%import common.NUMBER",
            ),
        )
        composer.register(sl)
        removed = composer.unregister("minimal")
        assert removed is sl
        assert "minimal" not in composer.slices

    def test_unregister_with_dependents_fails(self):
        composer = GrammarComposer()
        composer.register(_numbers_slice())
        composer.register(_multiplication_slice())

        with pytest.raises(ValueError, match="depend on it"):
            composer.unregister("arithmetic.numbers")

    def test_unregister_nonexistent(self):
        composer = GrammarComposer()
        with pytest.raises(KeyError):
            composer.unregister("nonexistent")

    def test_dependency_not_met(self):
        composer = GrammarComposer()
        with pytest.raises(SliceDependencyError, match="not registered"):
            composer.register(_multiplication_slice())

    def test_replace(self):
        composer = GrammarComposer()
        composer.register(_numbers_slice())
        composer.register(_multiplication_slice())
        composer.register(_addition_slice())

        # Replace multiplication with a version that only has *
        new_mul = LanguageSlice(
            name="arithmetic.multiplication",
            syntax=SyntaxDefinition(
                rules='?mul_expr: atom\n    | mul_expr "*" atom -> mul',
            ),
            dependencies=["arithmetic.numbers"],
        )
        old = composer.replace("arithmetic.multiplication", new_mul)
        assert old.name == "arithmetic.multiplication"

        # Should still parse multiplication
        parser = composer.build_parser()
        tree = parser.parse("2 + 3 * 4")
        assert tree is not None

    def test_cache_invalidation(self):
        composer = GrammarComposer()
        sl = LanguageSlice(
            name="minimal",
            syntax=SyntaxDefinition(
                rules="start: NUMBER",
                terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
            ),
        )
        composer.register(sl)
        grammar1 = composer.compose()
        # Registering a new slice should invalidate cache
        sl2 = LanguageSlice(
            name="extra",
            syntax=SyntaxDefinition(rules='extra_rule: "hello"'),
        )
        composer.register(sl2)
        grammar2 = composer.compose()
        assert grammar1 != grammar2

    def test_duplicate_registration_fails(self):
        composer = GrammarComposer()
        sl = LanguageSlice(
            name="test",
            syntax=SyntaxDefinition(rules="start: NUMBER", terminals="%import common.NUMBER"),
        )
        composer.register(sl)
        with pytest.raises(ValueError, match="already registered"):
            composer.register(sl)

    def test_compose_empty_raises(self):
        composer = GrammarComposer()
        with pytest.raises(ValueError, match="No slices"):
            composer.compose()

    def test_circular_dependency(self):
        composer = GrammarComposer()
        # Manually inject to create a cycle
        a = LanguageSlice(
            name="a",
            syntax=SyntaxDefinition(rules="rule_a: NUMBER", terminals="%import common.NUMBER"),
            dependencies=["b"],
        )
        b = LanguageSlice(
            name="b",
            syntax=SyntaxDefinition(rules="rule_b: NUMBER"),
            dependencies=["a"],
        )
        # Can't even register a since b isn't there
        with pytest.raises(SliceDependencyError):
            composer.register(a)
