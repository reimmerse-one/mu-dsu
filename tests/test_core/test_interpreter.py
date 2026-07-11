"""Tests for Interpreter — basic dispatch and phase ordering."""

from lark import Tree

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Context, Interpreter
from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def _make_minimal_interpreter() -> Interpreter:
    """Interpreter with a minimal grammar: just numbers."""
    composer = GrammarComposer()
    composer.register(
        LanguageSlice(
            name="minimal",
            syntax=SyntaxDefinition(
                rules="start: NUMBER",
                terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
            ),
        )
    )
    actions = ActionRegistry()
    return Interpreter(composer, actions)


class TestInterpreter:
    def test_load_and_parse(self):
        interp = _make_minimal_interpreter()
        tree = interp.load("42")
        assert tree.data == "start"

    def test_run_default_visits_children(self):
        """Without any actions, the interpreter visits children and returns token values."""
        interp = _make_minimal_interpreter()
        result = interp.run("42")
        assert result == 42

    def test_replace_action(self):
        """A replace action overrides default child visitation."""
        composer = GrammarComposer()
        composer.register(
            LanguageSlice(
                name="nums",
                syntax=SyntaxDefinition(
                    rules="start: NUMBER -> number",
                    terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
                ),
            )
        )
        actions = ActionRegistry()
        actions.register(
            SemanticAction(
                node_type="number",
                role="execution",
                phase="replace",
                handler=lambda node, ctx, visit: int(node.children[0]) * 10,
            )
        )
        interp = Interpreter(composer, actions)
        result = interp.run("5")
        assert result == 50

    def test_before_and_after_phases(self):
        """Before runs before replace, after runs after and can transform the result."""
        composer = GrammarComposer()
        composer.register(
            LanguageSlice(
                name="nums",
                syntax=SyntaxDefinition(
                    rules="start: NUMBER -> number",
                    terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
                ),
            )
        )

        log: list[str] = []

        def before_handler(node: Tree, ctx: Context) -> None:
            log.append("before")

        def replace_handler(node: Tree, ctx: Context, visit):
            log.append("replace")
            return int(node.children[0])

        def after_handler(node: Tree, ctx: Context, visit, result):
            log.append("after")
            return result + 1  # Transform result

        actions = ActionRegistry()
        actions.register(
            SemanticAction(
                node_type="number", role="execution", phase="before",
                handler=before_handler, id="b",
            )
        )
        actions.register(
            SemanticAction(
                node_type="number", role="execution", phase="replace",
                handler=replace_handler, id="r",
            )
        )
        actions.register(
            SemanticAction(
                node_type="number", role="execution", phase="after",
                handler=after_handler, id="a",
            )
        )

        interp = Interpreter(composer, actions)
        result = interp.run("7")
        assert log == ["before", "replace", "after"]
        assert result == 8  # 7 + 1

    def test_no_program_raises(self):
        interp = _make_minimal_interpreter()
        try:
            interp.run()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "No program loaded" in str(e)

    def test_invalidate_parser(self):
        interp = _make_minimal_interpreter()
        interp.load("42")
        interp.invalidate_parser()
        # Parser should be rebuilt on next load
        tree = interp.load("99")
        assert tree is not None


class TestUpdatePoints:
    """Sect. 4.2 of the paper: an event 'blocks the interpretation of the
    application' and 'the interpretation is resumed from the point of the
    previous suspension, but using the adapted interpreter'.

    Every node visit is an update point: pause() from another thread blocks
    execution there; resume() continues it in place — no restart.
    """

    PROGRAM = "var i = 0;\nfor (var k = 0; k < 3000; ++k) {\n    i = i + 1;\n};\n"

    def _make_calc_interpreter(self) -> Interpreter:
        from mu_dsu.languages.calc_lang import compose_calclang

        composer, actions = compose_calclang()
        return Interpreter(composer, actions)

    def test_pause_blocks_at_update_point_resume_continues(self):
        import threading
        import time

        interp = self._make_calc_interpreter()
        visits = {"n": 0}
        progressed = threading.Event()

        def probe(node, ctx):
            visits["n"] += 1
            if visits["n"] >= 20:
                progressed.set()

        interp.actions.register(
            SemanticAction(
                node_type="assign_stmt", role="execution", phase="before",
                handler=probe, id="test.update_point.probe",
            )
        )

        worker = threading.Thread(target=lambda: interp.run(self.PROGRAM))
        worker.start()
        assert progressed.wait(timeout=15), "worker never started visiting nodes"

        interp.pause()
        time.sleep(0.1)  # let the worker reach its next update point
        frozen_at = visits["n"]
        time.sleep(0.2)
        # Blocked at an update point: no further visits while paused
        # (allow one in-flight visit that had already passed the check)
        assert visits["n"] <= frozen_at + 1
        assert worker.is_alive(), "worker must be suspended, not finished"

        interp.resume()
        worker.join(timeout=15)
        assert not worker.is_alive(), "worker must complete after resume"
        # Resumed from the suspension point — the full computation finished
        assert interp.env.get("i") == 3000

    def test_pause_resume_flags(self):
        interp = self._make_calc_interpreter()
        assert not interp.is_paused
        interp.pause()
        assert interp.is_paused
        interp.resume()
        assert not interp.is_paused
        assert not interp.is_running
