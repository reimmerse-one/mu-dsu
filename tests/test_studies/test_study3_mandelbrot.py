"""Study 3 tests: Mandelbrot Localised Adaptation (for -> parfor)."""

from mu_dsu.studies.study3_mandelbrot.programs import MANDELBROT_PROGRAM, NESTED_FOR_SIMPLE
from mu_dsu.studies.study3_mandelbrot.study import MandelbrotStudy


class TestSequentialExecution:
    def test_nested_for_sequential(self):
        study = MandelbrotStudy()
        study.run(NESTED_FOR_SIMPLE)
        assert study.interpreter.env.get("total") == 12
        # 1 outer for + 3 inner for invocations = 4 sequential
        assert all(m == "sequential" for m in study.execution_modes)

    def test_mandelbrot_runs(self):
        study = MandelbrotStudy()
        study.run(MANDELBROT_PROGRAM)
        assert study.interpreter.env.get("HEIGHT") == 5


class TestLocalisedAdaptation:
    def test_only_inner_for_parallelised(self):
        """The key Study 3 result: localised adaptation targets only inner for."""
        study = MandelbrotStudy()
        study.run(NESTED_FOR_SIMPLE)

        # Before: all sequential
        assert all(m == "sequential" for m in study.execution_modes)

        # Apply localised adaptation
        assert study.adapt_localised()

        # Re-run WITHOUT reparsing (reuse adapted parse tree)
        study.interpreter.env.set("total", 0)
        study.run()

        # After: outer=sequential, inner=parallel
        modes = study.execution_modes
        assert "sequential" in modes  # outer for
        assert "parallel" in modes    # inner for

    def test_result_identical(self):
        """Parallel version produces same result as sequential."""
        study = MandelbrotStudy()
        study.run(NESTED_FOR_SIMPLE)
        result_seq = study.interpreter.env.get("total")

        study.adapt_localised()
        study.interpreter.env.set("total", 0)
        study.run()  # reuse adapted parse tree
        result_par = study.interpreter.env.get("total")

        assert result_seq == result_par == 12


class TestSystemWideComparison:
    def test_system_wide_parallelises_all(self):
        """System-wide: ALL for loops become parallel."""
        study = MandelbrotStudy()
        study.run(NESTED_FOR_SIMPLE)
        study.adapt_system_wide()

        # redo re-ran the program — check only post-adaptation modes
        # Re-run fresh to get clean modes
        study.run(NESTED_FOR_SIMPLE)
        assert all(m == "parallel" for m in study.execution_modes)

    def test_localised_vs_system_wide(self):
        """Localised is more precise: only inner for becomes parallel."""
        # System-wide: all parallel
        study_sw = MandelbrotStudy()
        study_sw.run(NESTED_FOR_SIMPLE)
        study_sw.adapt_system_wide()
        study_sw.run(NESTED_FOR_SIMPLE)
        assert all(m == "parallel" for m in study_sw.execution_modes)

        # Localised: mix of sequential (outer) and parallel (inner)
        study_loc = MandelbrotStudy()
        study_loc.run(NESTED_FOR_SIMPLE)
        study_loc.adapt_localised()
        study_loc.interpreter.env.set("total", 0)
        study_loc.run()  # reuse adapted parse tree
        modes = study_loc.execution_modes
        assert "sequential" in modes
        assert "parallel" in modes
        # Outer=1 sequential, inner=3 parallel
        assert modes.count("sequential") == 1
        assert modes.count("parallel") == 3
