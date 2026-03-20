"""Integration tests — μDA scripts executed against HooverLang interpreter."""

import pytest

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.core.slice import SemanticAction
from mu_dsu.languages.state_machine import compose_hooverlang, create_runner
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice


class TestSystemWideAdaptation:
    """System-wide: replace slice + redo role evaluation."""

    def test_replace_state_slice_with_standby(self):
        """Core Phase 3 validation: μDA script replaces state slice semantics.

        Before adaptation: default vacuum cleaner, no standby awareness.
        After adaptation: entering 'on' state also sets __sm_standby_enabled__.
        """
        # Create interpreter with default HooverLang
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)

        # Load default program
        interp.run(DEFAULT_PROGRAM)
        assert not interp.env.has("__sm_standby_enabled__")

        # Execute μDA adaptation script
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })

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
        result = adapter.adapt(script, interp)
        assert result.success
        assert any("replace_slice" in op for op in result.operations_applied)
        assert any("redo" in op for op in result.operations_applied)

        # After adaptation: standby flag should be set (since redo re-processed 'on' state)
        assert interp.env.has("__sm_standby_enabled__")
        assert interp.env.get("__sm_standby_enabled__") is True

    def test_redo_reprocesses_declarations(self):
        """After slice replacement, redo re-runs declarations with new semantics."""
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        interp.run(DEFAULT_PROGRAM)

        states_before = dict(interp.env.get("__sm_states__"))

        # Replace with standby slice and redo
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
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
        adapter.adapt(script, interp)

        # States should be repopulated (new slice's action ran)
        states_after = interp.env.get("__sm_states__")
        assert "on" in states_after
        assert "off" in states_after

    def test_adaptation_result_reports_operations(self):
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        interp.run(DEFAULT_PROGRAM)

        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
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
        result = adapter.adapt(script, interp)
        assert result.success
        assert len(result.operations_applied) == 2


class TestLocalisedAdaptation:
    """Localised: match specific parse tree nodes, modify actions for those only."""

    def test_add_before_action_to_specific_node(self):
        """Add a 'before' action to state_def nodes only."""
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        interp.run(DEFAULT_PROGRAM)

        log: list[str] = []

        # Create a before action that logs state registration
        log_action = SemanticAction(
            node_type="state_def",
            role="execution",
            phase="before",
            handler=lambda node, ctx: log.append(f"visiting:{node.children[0]}"),
            id="log_state_visit",
        )

        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state": interp.composer.slices["sm.state"],
        })

        # Register the action in a slice for context resolution
        from mu_dsu.core.slice import LanguageSlice, SyntaxDefinition
        log_slice = LanguageSlice(
            name="sm.state.log",
            syntax=SyntaxDefinition(rules='_unused_log: "NEVERMATCHES"'),
            actions=[log_action],
        )
        adapter._slice_registry["sm.state.log"] = log_slice

        script = """
        context {
            action logAct : state_def from module sm.state.log role execution;
        }
        when state_def occurs {
            add action logAct in role execution;
        }
        """
        result = adapter.adapt(script, interp)
        assert result.success
        assert len(result.operations_applied) >= 1

    def test_reachable_path_match(self):
        """Match trans_rule nodes within a specific trans_def subtree."""
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        interp.run(DEFAULT_PROGRAM)

        from mu_dsu.adaptation.matcher import ParseTreeMatcher
        from mu_dsu.adaptation.context import ResolvedContext
        from mu_dsu.adaptation.operations import NodeMatch, ReachablePathMatch

        matcher = ParseTreeMatcher()
        ctx = ResolvedContext()

        # Find all trans_rule nodes reachable FROM transitions_section
        # id1 << id2 means "from id1 you can reach id2"
        expr = ReachablePathMatch(
            descendant=NodeMatch(name="transitions_section"),
            ancestor=NodeMatch(name="trans_rule"),
        )
        results = matcher.match(expr, interp.parse_tree, ctx)
        # Default program has 2 transitions: on{click=>off}, off{click=>on}
        assert len(results) == 2


class TestRoundTrip:
    """End-to-end: parse script → resolve context → execute → verify behaviour change."""

    def test_full_roundtrip_with_runner(self):
        """Full round-trip: load default program, adapt, verify new behaviour."""
        from mu_dsu.languages.state_machine.runner import StateMachineRunner

        # Create and load
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        runner = StateMachineRunner(interp)
        runner.load(DEFAULT_PROGRAM)
        assert runner.current_state == "on"

        # Adapt
        adapter = MicroLanguageAdapter(slice_registry={
            "sm.state_standby": state_standby_slice(),
        })
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
        result = adapter.adapt(script, interp)
        assert result.success

        # After adaptation, the interpreter has new semantics
        # The runner can still execute with the adapted interpreter
        assert interp.env.get("__sm_standby_enabled__") is True
