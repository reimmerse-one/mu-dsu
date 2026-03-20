"""Input→Output verification against the paper.

These tests feed EXACT inputs described in the paper into our system
and verify the outputs match what the paper describes.
Not structure checks — actual program execution with observable results.
"""

from mu_dsu.adaptation.adapter import MicroLanguageAdapter
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.calc_lang import compose_calclang
from mu_dsu.languages.calc_lang.slices.par_for_loop import par_for_loop_slice
from mu_dsu.languages.mini_js import compose_mini_js
from mu_dsu.languages.mini_js.slices.print_blind import print_blind_slice
from mu_dsu.languages.mini_js.slices.print_hyperopic import print_hyperopic_slice
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.runner import StateMachineRunner
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice


# ============================================================================
# Fig. 2(a) — Vacuum Cleaner Default: input=click sequence → output=state trace
#
# Paper Fig. 2(a) shows the state diagram:
#   on ←click→ off
# So: click,click,click,click → off,on,off,on
# ============================================================================

class TestIO_Fig2a_VacuumDefault:
    """Input: sequence of click events.
    Output: sequence of states visited.
    """

    def _run_with_clicks(self, click_sequence: list[bool]) -> list[str]:
        """Feed a click sequence, return the state trace."""
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        idx = [0]

        def next_click():
            if idx[0] < len(click_sequence):
                val = click_sequence[idx[0]]
                idx[0] += 1
                return val
            return False

        interp.env.set_global("get.click", next_click)
        from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
        runner = StateMachineRunner(interp)
        runner.load(DEFAULT_PROGRAM)

        trace = [runner.current_state]
        for _ in range(len(click_sequence)):
            result = runner.step()
            trace.append(runner.current_state)
        return trace

    def test_four_clicks(self):
        """Input:  [True, True, True, True]
        Output: on → off → on → off → on
        """
        trace = self._run_with_clicks([True, True, True, True])
        assert trace == ["on", "off", "on", "off", "on"]

    def test_no_clicks(self):
        """Input:  [False, False, False]
        Output: on → on → on → on  (no transitions fire)
        """
        trace = self._run_with_clicks([False, False, False])
        assert trace == ["on", "on", "on", "on"]

    def test_mixed_clicks(self):
        """Input:  [False, True, False, True]
        Output: on → on → off → off → on
        """
        trace = self._run_with_clicks([False, True, False, True])
        assert trace == ["on", "on", "off", "off", "on"]


# ============================================================================
# Fig. 2(b) — Vacuum Cleaner with Stand-by
#
# Paper Sect. 3.2 describes the scenario:
#   "if it is not in motion for 10 seconds, it is considered not in use"
#   on →inactivity→ stand-by →(repeat, t increments)→ stand-by →elapsed(t>10)→ off
#
# Input: inactivity fires continuously, no clicks, no activity
# Output: on → stand-by → stand-by → ... (11 times) → off
# ============================================================================

class TestIO_Fig2b_VacuumStandby:
    """Input: inactivity event sequence.
    Output: state trace showing stand-by then timeout to off.
    """

    def test_inactivity_timeout_scenario(self):
        """Input:  inactivity=True every step, no clicks, no activity
        Output: on, stand-by, stand-by, ..., stand-by (11 steps), off

        Paper: 't > 10' means after 11 increments in stand-by (t goes 1,2,...,11),
        elapsed fires and transitions to off.
        """
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        interp.env.set_global("get.activity", lambda: False)
        interp.env.set_global("get.time", lambda: True)

        from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM
        runner = StateMachineRunner(interp)
        runner.load(STANDBY_PROGRAM)

        trace = [runner.current_state]
        for _ in range(20):
            runner.step()
            trace.append(runner.current_state)
            if runner.current_state == "off":
                break

        # Verify the exact trace
        assert trace[0] == "on"
        assert trace[1] == "stand-by"      # first inactivity
        assert all(s == "stand-by" for s in trace[2:12])  # t=2..11
        assert trace[12] == "off"           # t=12 > 10, elapsed fires

    def test_activity_returns_to_on(self):
        """Input:  inactivity → stand-by, then activity fires
        Output: on → stand-by → on

        Paper Fig. 2(b): activity arrow from stand-by to on.
        """
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        activity_flag = [False]
        interp.env.set_global("get.click", lambda: False)
        interp.env.set_global("get.activity", lambda: activity_flag[0])
        interp.env.set_global("get.time", lambda: True)

        from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM
        runner = StateMachineRunner(interp)
        runner.load(STANDBY_PROGRAM)

        assert runner.current_state == "on"
        runner.step()  # → stand-by
        assert runner.current_state == "stand-by"

        # Now activity fires, inactivity stops → should go back to on
        # (inactivity is checked before activity in transition list,
        #  so inactivity must be off for activity to trigger)
        interp.env.set_global("get.time", lambda: False)
        activity_flag[0] = True
        runner.step()
        assert runner.current_state == "on"

        # And t should be reset to 0 (on = turn-on ; t <- 0)
        assert interp.env.get("t") == 0

    def test_click_from_standby_goes_to_off(self):
        """Paper: stand-by { click => off ; ... }
        Input:  enter stand-by, then click
        Output: stand-by → off
        """
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        click_flag = [False]
        interp.env.set_global("get.click", lambda: click_flag[0])
        interp.env.set_global("get.activity", lambda: False)
        interp.env.set_global("get.time", lambda: True)

        from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM
        runner = StateMachineRunner(interp)
        runner.load(STANDBY_PROGRAM)

        runner.step()  # on → stand-by
        assert runner.current_state == "stand-by"

        click_flag[0] = True
        runner.step()  # click → off
        assert runner.current_state == "off"


# ============================================================================
# Sect. 5.1 — HTML Viewer: input=program text → output=rendered result
#
# Paper Listing 4 (simplified):
#   set font color parsed.color; set font size parsed.size; print parsed.text;
#
# Output varies by profile:
#   healthy:  {text="Hello", size=12, color="red"}
#   hyperopic: {text="Hello", size=36, color="red"}  ← size * 3
#   blind:    {text="Hello", size=12, color="red"} + speech=["Hello"]
# ============================================================================

class TestIO_Sect51_HTMLViewer:
    """Input: a viewer program with specific text/size/color.
    Output: rendered output entries and optionally speech buffer.
    """

    PROGRAM = 'var c = "red"; var s = 12; var t = "Hello"; set font color c; set font size s; print t;'

    def test_healthy_output(self):
        """Input:  program above with healthy profile
        Output: [{text="Hello", size=12, color="red", profile="healthy"}]
        """
        composer, actions = compose_mini_js()
        interp = Interpreter(composer, actions)
        interp.run(self.PROGRAM)
        output = interp.env.get("__output__")

        assert len(output) == 1
        assert output[0] == {
            "text": "Hello",
            "size": 12,
            "color": "red",
            "profile": "healthy",
        }

    def test_hyperopic_output(self):
        """Input:  same program, after healthy→hyperopic adaptation
        Output: [{text="Hello", size=36, color="red", profile="hyperopic"}]

        Paper p.15: "multiplied by 3 to increase the size"
        12 * 3 = 36
        """
        composer, actions = compose_mini_js()
        interp = Interpreter(composer, actions)
        interp.run(self.PROGRAM)

        adapter = MicroLanguageAdapter(slice_registry={
            "viewer.print_hyperopic": print_hyperopic_slice(),
        })
        adapter.adapt("""
            context { slice old: viewer.print; slice new: viewer.print_hyperopic; }
            system-wide { replace slice old with new; redo role execution; }
        """, interp)

        output = interp.env.get("__output__")
        hyperopic = [o for o in output if o["profile"] == "hyperopic"]
        assert len(hyperopic) == 1
        assert hyperopic[0]["text"] == "Hello"
        assert hyperopic[0]["size"] == 36   # 12 * 3
        assert hyperopic[0]["color"] == "red"

    def test_blind_output(self):
        """Input:  same program, after healthy→blind adaptation
        Output: [{text="Hello", ...profile="blind"}] AND speech=["Hello"]

        Paper p.15: "reads it aloud using a specific library"
        """
        composer, actions = compose_mini_js()
        interp = Interpreter(composer, actions)
        interp.run(self.PROGRAM)

        adapter = MicroLanguageAdapter(slice_registry={
            "viewer.print_blind": print_blind_slice(),
        })
        adapter.adapt("""
            context { slice old: viewer.print; slice new: viewer.print_blind; }
            system-wide { replace slice old with new; redo role execution; }
        """, interp)

        output = interp.env.get("__output__")
        blind = [o for o in output if o["profile"] == "blind"]
        assert len(blind) == 1
        assert blind[0]["text"] == "Hello"

        speech = interp.env.get("__speech__")
        assert speech == ["Hello"]

    def test_system_wide_all_prints_change(self):
        """Input:  program with TWO print statements, adapt to blind
        Output: BOTH prints appear as blind, BOTH are spoken

        Paper p.15: "the change will affect all uses of the changed language features"
        """
        program = 'set font size 10; print "line1"; print "line2";'
        composer, actions = compose_mini_js()
        interp = Interpreter(composer, actions)
        interp.run(program)

        adapter = MicroLanguageAdapter(slice_registry={
            "viewer.print_blind": print_blind_slice(),
        })
        adapter.adapt("""
            context { slice old: viewer.print; slice new: viewer.print_blind; }
            system-wide { replace slice old with new; redo role execution; }
        """, interp)

        output = interp.env.get("__output__")
        blind = [o for o in output if o["profile"] == "blind"]
        assert len(blind) == 2
        assert blind[0]["text"] == "line1"
        assert blind[1]["text"] == "line2"

        speech = interp.env.get("__speech__")
        assert speech == ["line1", "line2"]


# ============================================================================
# Sect. 3.2 + Sect. 5.1 — Seamless Adaptation I/O
#
# Paper's key claim: "any program written in this language will remain
# unaltered, yet will incorporate the new behaviour"
#
# Input:  (1) run program with default semantics → observe output A
#         (2) apply μDA adaptation (no program change)
#         (3) re-run SAME program text → observe output B
# Output: A ≠ B, but program text is identical
# ============================================================================

class TestIO_SeamlessAdaptation:
    """Same input (program text), different output after adaptation."""

    def test_same_program_different_output(self):
        """Input:  identical program text, run twice
        Before adaptation: output has size=12
        After adaptation:  output has size=36

        The program text is CHARACTER-FOR-CHARACTER identical.
        """
        program = 'set font size 12; print "test";'

        # Run 1: healthy
        c1, a1 = compose_mini_js()
        i1 = Interpreter(c1, a1)
        i1.run(program)
        out_before = i1.env.get("__output__")[0]

        # Run 2: same program, but with hyperopic semantics
        c2, a2 = compose_mini_js()
        i2 = Interpreter(c2, a2)
        adapter = MicroLanguageAdapter(slice_registry={
            "viewer.print_hyperopic": print_hyperopic_slice(),
        })
        # Adapt BEFORE running
        i2.run(program)
        adapter.adapt("""
            context { slice old: viewer.print; slice new: viewer.print_hyperopic; }
            system-wide { replace slice old with new; redo role execution; }
        """, i2)
        out_after = [o for o in i2.env.get("__output__") if o["profile"] == "hyperopic"][0]

        # Same text, same color — different size
        assert out_before["text"] == out_after["text"] == "test"
        assert out_before["size"] == 12
        assert out_after["size"] == 36
        # Program text was identical
        assert program == program  # tautology, but the point is we never modified it


# ============================================================================
# Sect. 5.2 + Fig. 5 — Mandelbrot: for→parfor I/O
#
# Input:  nested for program (3 outer × 4 inner iterations)
# Output before: total=12, all execution modes = "sequential"
# Output after localised adaptation: total=12, outer=sequential, inner=parallel
# Output after system-wide adaptation: total=12, all modes = "parallel"
#
# Paper p.18: "Instead to get the desired evolution (Fig. 5(c)) with only
# the second occurrence of the for language feature replaced..."
# ============================================================================

class TestIO_Sect52_Mandelbrot:
    """Input: nested for program.
    Output: computation result + execution mode trace.
    """

    PROGRAM = """\
var total = 0;
for (var i = 0; i < 3; ++i) {
    for (var j = 0; j < 4; ++j) {
        total = total + 1;
    };
};
"""

    def test_sequential_io(self):
        """Input:  nested for, no adaptation
        Output: total=12, modes=[seq, seq, seq, seq] (1 outer + 3 inner)
        """
        composer, actions = compose_calclang()
        interp = Interpreter(composer, actions)
        interp.env.set("__exec_modes__", [])
        interp.run(self.PROGRAM)

        assert interp.env.get("total") == 12
        modes = interp.env.get("__exec_modes__")
        assert all(m == "sequential" for m in modes)

    def test_system_wide_io(self):
        """Input:  nested for + system-wide for→parfor
        Output: total=12 (same!), but ALL modes are parallel

        Paper Fig. 5(b): "only parfor" — all nodes become green.
        """
        composer, actions = compose_calclang()
        interp = Interpreter(composer, actions)
        interp.env.set("__exec_modes__", [])
        interp.run(self.PROGRAM)
        assert interp.env.get("total") == 12

        adapter = MicroLanguageAdapter(slice_registry={
            "calc.par_for_loop": par_for_loop_slice(),
        })
        adapter.adapt("""
            context { slice old: calc.for_loop; slice new: calc.par_for_loop; }
            system-wide { replace slice old with new; redo role execution; }
        """, interp)

        # Re-run to get clean modes
        interp.env.set("__exec_modes__", [])
        interp.env.set("total", 0)
        interp.run(self.PROGRAM)

        assert interp.env.get("total") == 12  # Same result!
        modes = interp.env.get("__exec_modes__")
        assert all(m == "parallel" for m in modes)

    def test_localised_io(self):
        """Input:  nested for + localised inner-only for→parfor
        Output: total=12 (same!), outer=sequential, inner=parallel

        Paper Fig. 5(c): "for+parfor" — outer purple (seq), inner green (par).
        """
        from mu_dsu.studies.study3_mandelbrot.study import MandelbrotStudy
        study = MandelbrotStudy()
        study.run(self.PROGRAM)
        assert study.interpreter.env.get("total") == 12

        study.adapt_localised()
        study.interpreter.env.set("total", 0)
        study.run()  # reuse adapted parse tree

        assert study.interpreter.env.get("total") == 12  # Same result!
        modes = study.execution_modes
        assert modes.count("sequential") == 1   # outer for
        assert modes.count("parallel") == 3     # inner for (3 invocations)

    def test_localised_vs_system_wide_same_result_different_execution(self):
        """Paper's key point: both produce total=12, but execution strategy differs.

        System-wide: ALL for → parfor (wrong for dependent loops)
        Localised:   only inner for → parfor (correct, selective)
        """
        # System-wide
        c1, a1 = compose_calclang()
        i1 = Interpreter(c1, a1)
        i1.env.set("__exec_modes__", [])
        i1.run(self.PROGRAM)
        adapter = MicroLanguageAdapter(slice_registry={"calc.par_for_loop": par_for_loop_slice()})
        adapter.adapt("""
            context { slice old: calc.for_loop; slice new: calc.par_for_loop; }
            system-wide { replace slice old with new; redo role execution; }
        """, i1)
        i1.env.set("__exec_modes__", [])
        i1.env.set("total", 0)
        i1.run(self.PROGRAM)
        total_sw = i1.env.get("total")
        parallel_count_sw = i1.env.get("__exec_modes__").count("parallel")

        # Localised
        from mu_dsu.studies.study3_mandelbrot.study import MandelbrotStudy
        study = MandelbrotStudy()
        study.run(self.PROGRAM)
        study.adapt_localised()
        study.interpreter.env.set("total", 0)
        study.run()
        total_loc = study.interpreter.env.get("total")
        parallel_count_loc = study.execution_modes.count("parallel")
        seq_count_loc = study.execution_modes.count("sequential")

        # Same computation result
        assert total_sw == total_loc == 12

        # Different execution strategy
        assert parallel_count_sw == 4   # ALL for loops parallel
        assert parallel_count_loc == 3  # only inner for parallel
        assert seq_count_loc == 1       # outer for still sequential
