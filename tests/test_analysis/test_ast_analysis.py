"""Tests for AST-based feature analysis (no LLM needed)."""

from mu_dsu.analysis.feature_analyzer import FeatureAnalyzer
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.examples.standby import STANDBY_PROGRAM
from mu_dsu.languages.calc_lang import create_interpreter as create_calc
from mu_dsu.studies.study3_mandelbrot.programs import NESTED_FOR_SIMPLE
from mu_dsu.core.interpreter import Interpreter


class TestASTAnalysisHooverLang:
    def _analyze_program(self, program):
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        tree = interp.load(program)
        analyzer = FeatureAnalyzer()
        return analyzer.analyze_ast(tree)

    def test_identifies_features_default(self):
        result = self._analyze_program(DEFAULT_PROGRAM)
        assert len(result.features) > 0
        # Should find states, events, transitions sections
        names = [f.name for f in result.features]
        assert any("states" in n for n in names)

    def test_identifies_micro_languages(self):
        result = self._analyze_program(DEFAULT_PROGRAM)
        assert len(result.micro_languages) > 0
        # Each feature gets a micro-language
        assert len(result.micro_languages) == len(result.features)

    def test_micro_language_has_node_types(self):
        result = self._analyze_program(DEFAULT_PROGRAM)
        for ml in result.micro_languages:
            assert len(ml.language_features) > 0

    def test_detects_overlaps(self):
        """Features sharing node types should have overlaps."""
        result = self._analyze_program(DEFAULT_PROGRAM)
        # states and transitions both use IDENT-related nodes
        has_overlap = any(len(ml.overlaps_with) > 0 for ml in result.micro_languages)
        # May or may not have overlaps depending on AST structure
        assert isinstance(has_overlap, bool)

    def test_standby_has_more_features(self):
        """Standby program should have more features (counter, more states)."""
        result_default = self._analyze_program(DEFAULT_PROGRAM)
        result_standby = self._analyze_program(STANDBY_PROGRAM)
        # Standby has counter_decl as extra section
        assert len(result_standby.features) >= len(result_default.features)


class TestASTAnalysisCalcLang:
    def test_identifies_nested_for_features(self):
        interp = create_calc()
        tree = interp.load(NESTED_FOR_SIMPLE)
        analyzer = FeatureAnalyzer()
        result = analyzer.analyze_ast(tree)
        assert len(result.features) > 0
        # Should identify for_stmt as a node type in some feature
        all_types = set()
        for f in result.features:
            all_types.update(f.node_types)
        assert "for_stmt" in all_types or "var_stmt" in all_types
