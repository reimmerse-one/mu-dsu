"""Tests for HooverLang grammar composition and parsing."""

import pytest

from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM


@pytest.fixture
def parser():
    composer, _ = compose_hooverlang()
    return composer.build_parser()


class TestGrammarComposition:
    def test_compose_without_conflicts(self):
        """All 10 slices compose into a valid grammar."""
        composer, _ = compose_hooverlang()
        grammar = composer.compose()
        assert "start" in grammar
        assert "states_section" in grammar
        assert "events_section" in grammar
        assert "transitions_section" in grammar

    def test_parse_default_program(self, parser):
        """Listing 2a parses successfully."""
        tree = parser.parse(DEFAULT_PROGRAM)
        assert tree.data == "start"

    def test_parse_standby_program(self, parser):
        """Listing 2b parses successfully."""
        tree = parser.parse(STANDBY_PROGRAM)
        assert tree.data == "start"

    def test_hyphenated_identifiers(self, parser):
        """turn-on, turn-off, stand-by parse as single IDENT tokens."""
        tree = parser.parse(DEFAULT_PROGRAM)
        # Should find turn-on and turn-off in the tree
        flat = str(tree)
        assert "turn-on" in flat
        assert "turn-off" in flat

    def test_standby_has_counter(self, parser):
        """Listing 2b has a counter declaration."""
        tree = parser.parse(STANDBY_PROGRAM)
        flat = str(tree)
        assert "counter_decl" in flat

    def test_minimal_program(self, parser):
        """Minimal valid program."""
        program = """\
states
  idle = init
events
  go = get.go()
transitions
  idle { go => idle }
"""
        tree = parser.parse(program)
        assert tree.data == "start"
