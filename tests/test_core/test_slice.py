"""Tests for LanguageSlice, SyntaxDefinition, SemanticAction."""

import pytest

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


class TestSyntaxDefinition:
    def test_basic_construction(self):
        sd = SyntaxDefinition(rules='expr: NUMBER "+" NUMBER')
        assert "expr" in sd.rules
        assert sd.terminals == ""
        assert sd.priority == 0

    def test_with_terminals(self):
        sd = SyntaxDefinition(
            rules='expr: NUMBER "+" NUMBER',
            terminals="%import common.NUMBER",
        )
        assert "NUMBER" in sd.terminals


class TestSemanticAction:
    def test_valid_phases(self):
        for phase in ("before", "after", "replace"):
            action = SemanticAction(
                node_type="add", role="execution", phase=phase, handler=lambda *a: None
            )
            assert action.phase == phase

    def test_invalid_phase_raises(self):
        with pytest.raises(ValueError, match="Invalid phase"):
            SemanticAction(
                node_type="add", role="execution", phase="during", handler=lambda *a: None
            )

    def test_auto_generated_id(self):
        action = SemanticAction(
            node_type="mul", role="execution", phase="replace", handler=lambda *a: None
        )
        assert action.id == "mul.execution.replace"

    def test_explicit_id(self):
        action = SemanticAction(
            node_type="mul", role="execution", phase="replace",
            handler=lambda *a: None, id="custom_id",
        )
        assert action.id == "custom_id"


class TestLanguageSlice:
    def test_basic_construction(self):
        sl = LanguageSlice(
            name="test.numbers",
            syntax=SyntaxDefinition(rules="atom: NUMBER"),
            actions=[],
        )
        assert sl.name == "test.numbers"
        assert sl.dependencies == []

    def test_validate_passes(self):
        sl = LanguageSlice(
            name="test.numbers",
            syntax=SyntaxDefinition(rules="atom: NUMBER"),
        )
        sl.validate()  # Should not raise

    def test_validate_empty_name(self):
        sl = LanguageSlice(
            name="",
            syntax=SyntaxDefinition(rules="atom: NUMBER"),
        )
        with pytest.raises(ValueError, match="name must not be empty"):
            sl.validate()

    def test_validate_empty_rules(self):
        sl = LanguageSlice(
            name="test.empty",
            syntax=SyntaxDefinition(rules="   "),
        )
        with pytest.raises(ValueError, match="syntax rules must not be empty"):
            sl.validate()

    def test_with_dependencies(self):
        sl = LanguageSlice(
            name="test.addition",
            syntax=SyntaxDefinition(rules='expr: expr "+" atom'),
            dependencies=["test.numbers"],
        )
        assert sl.dependencies == ["test.numbers"]
