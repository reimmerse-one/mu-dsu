"""Tests for μDA grammar and parser."""

import pytest

from mu_dsu.adaptation.mu_da_parser import MuDaParser
from mu_dsu.adaptation.operations import (
    ActionBinding,
    AddAction,
    NonterminalBinding,
    NodeMatch,
    ParentPathMatch,
    ReachablePathMatch,
    RedoRole,
    RemoveAction,
    ReplaceSlice,
    SetSpecialized,
    SliceBinding,
    SystemWideClause,
    WhenClause,
)


@pytest.fixture
def parser():
    return MuDaParser()


class TestSystemWideScripts:
    def test_parse_replace_and_redo(self, parser):
        """Listing 6b equivalent: replace slice + redo."""
        script = """
        context {
            slice old: sm.state;
            slice new: sm.state_standby;
        }
        system-wide {
            replace slice old with new;
            redo role execution;
        }
        """
        result = parser.parse(script)
        assert len(result.context) == 2
        assert isinstance(result.context[0], SliceBinding)
        assert result.context[0].names == ["old"]
        assert result.context[0].qualified_name == "sm.state"
        assert isinstance(result.context[1], SliceBinding)
        assert result.context[1].names == ["new"]

        assert len(result.clauses) == 1
        clause = result.clauses[0]
        assert isinstance(clause, SystemWideClause)
        assert len(clause.operations) == 2
        assert isinstance(clause.operations[0], ReplaceSlice)
        assert clause.operations[0].old_name == "old"
        assert clause.operations[0].new_name == "new"
        assert isinstance(clause.operations[1], RedoRole)
        assert clause.operations[1].role == "execution"

    def test_parse_redo_without_args(self, parser):
        script = """
        context { slice x: some.slice; }
        system-wide { redo; }
        """
        result = parser.parse(script)
        redo = result.clauses[0].operations[0]
        assert isinstance(redo, RedoRole)
        assert redo.role is None
        assert redo.from_node is None

    def test_parse_redo_with_from(self, parser):
        script = """
        context { slice x: some.slice; }
        system-wide { redo from root role execution; }
        """
        result = parser.parse(script)
        redo = result.clauses[0].operations[0]
        assert redo.from_node == "root"
        assert redo.role == "execution"


class TestContextDefinitions:
    def test_multiple_slice_names(self, parser):
        script = """
        context {
            slice a, b: some.module;
        }
        system-wide { redo; }
        """
        result = parser.parse(script)
        binding = result.context[0]
        assert isinstance(binding, SliceBinding)
        assert binding.names == ["a", "b"]

    def test_nt_definition(self, parser):
        script = """
        context {
            nt x, y, z : ForStatement from module sm.control;
        }
        system-wide { redo; }
        """
        result = parser.parse(script)
        nt = result.context[0]
        assert isinstance(nt, NonterminalBinding)
        assert nt.names == ["x", "y", "z"]
        assert nt.rule_name == "ForStatement"
        assert nt.module_name == "sm.control"

    def test_action_definition(self, parser):
        script = """
        context {
            action myAction : state_def from module sm.state role execution;
        }
        system-wide { redo; }
        """
        result = parser.parse(script)
        act = result.context[0]
        assert isinstance(act, ActionBinding)
        assert act.name == "myAction"
        assert act.nonterminal == "state_def"
        assert act.module_name == "sm.state"
        assert act.role == "execution"

    def test_endemic_slice(self, parser):
        script = """
        context {
            endemic slice local: sm.state;
        }
        system-wide { redo; }
        """
        result = parser.parse(script)
        assert result.context[0].endemic is True


class TestLocalisedScripts:
    def test_when_clause_with_node_match(self, parser):
        script = """
        context {
            action myAct : state_def from module sm.state role execution;
        }
        when state_def occurs {
            add action myAct in role execution;
        }
        """
        result = parser.parse(script)
        clause = result.clauses[0]
        assert isinstance(clause, WhenClause)
        assert isinstance(clause.match_expr, NodeMatch)
        assert clause.match_expr.name == "state_def"
        assert len(clause.manipulations) == 1
        assert isinstance(clause.manipulations[0], AddAction)
        assert clause.manipulations[0].action_name == "myAct"
        assert clause.manipulations[0].role == "execution"

    def test_when_with_parent_path(self, parser):
        script = """
        context { slice x: sm.state; }
        when child < parent occurs {
            remove action act from target in role execution;
        }
        """
        result = parser.parse(script)
        clause = result.clauses[0]
        assert isinstance(clause.match_expr, ParentPathMatch)
        assert clause.match_expr.child.name == "child"
        assert clause.match_expr.parent.name == "parent"

    def test_when_with_reachable_path_and_filter(self, parser):
        """Listing 8 equivalent: for1 << for2 | for2"""
        script = """
        context {
            nt for1, for2 : trans_rule from module sm.transition;
            action parAct : trans_rule from module sm.transition role execution;
        }
        when for1 << for2 | for2 occurs {
            set specialized action for for2 to parAct in role execution;
        }
        """
        result = parser.parse(script)
        clause = result.clauses[0]
        assert isinstance(clause.match_expr, ReachablePathMatch)
        assert clause.match_expr.descendant.name == "for1"
        assert clause.match_expr.ancestor.name == "for2"
        assert clause.match_expr.filter_name == "for2"

        assert isinstance(clause.manipulations[0], SetSpecialized)
        assert clause.manipulations[0].nonterminal_name == "for2"
        assert clause.manipulations[0].action_name == "parAct"

    def test_node_match_with_conditions(self, parser):
        script = """
        context { slice x: sm.state; }
        when node[child0="on"] occurs {
            add action act in role execution;
        }
        """
        result = parser.parse(script)
        match = result.clauses[0].match_expr
        assert isinstance(match, NodeMatch)
        assert match.conditions == [("child0", '"on"')]

    def test_remove_action(self, parser):
        script = """
        context { slice x: sm.state; }
        when node occurs {
            remove action old_act in role execution;
        }
        """
        result = parser.parse(script)
        manip = result.clauses[0].manipulations[0]
        assert isinstance(manip, RemoveAction)
        assert manip.action_name == "old_act"


class TestComments:
    def test_comments_ignored(self, parser):
        script = """
        // This is a comment
        context {
            slice old: sm.state; // inline comment
        }
        // Another comment
        system-wide {
            redo;
        }
        """
        result = parser.parse(script)
        assert len(result.context) == 1
        assert len(result.clauses) == 1
