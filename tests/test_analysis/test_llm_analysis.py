"""Tests for LLM-assisted feature analysis (requires OPENROUTER_API_KEY).

These tests make real API calls. Skip if no API key is set.
"""

import os
import pytest

from mu_dsu.analysis.feature_analyzer import FeatureAnalyzer
from mu_dsu.analysis.llm_client import LLMClient
from mu_dsu.core.interpreter import Interpreter
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM


def _has_api_key() -> bool:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    return bool(os.environ.get("OPENROUTER_API_KEY"))


requires_api = pytest.mark.skipif(
    not _has_api_key(),
    reason="OPENROUTER_API_KEY not set"
)


@requires_api
class TestLLMClient:
    def test_basic_query(self):
        client = LLMClient()
        response = client.ask("What is 2+2? Reply with just the number.")
        assert "4" in response

    def test_json_response(self):
        client = LLMClient()
        response = client.ask_json(
            'Return a JSON object with key "answer" and value 42.'
        )
        assert "42" in response


@requires_api
class TestLLMFeatureAnalysis:
    def _make_hooverlang_tree(self):
        composer, actions = compose_hooverlang()
        interp = Interpreter(composer, actions)
        interp.env.set_global("get.click", lambda: False)
        tree = interp.load(DEFAULT_PROGRAM)
        return tree

    def test_analyze_with_llm(self):
        """LLM identifies features in the vacuum cleaner program."""
        tree = self._make_hooverlang_tree()
        llm = LLMClient()
        analyzer = FeatureAnalyzer(llm=llm)

        result = analyzer.analyze_with_llm(
            source=DEFAULT_PROGRAM,
            parse_tree=tree,
            language_description="A state machine language for appliance control. "
            "Has states (with initialization actions), events (with conditions), "
            "and transitions (event => target_state).",
        )

        assert len(result.features) > 0
        assert result.raw_llm_response  # Got a response
        # LLM should identify at least states and transitions
        feature_names = [f.name.lower() for f in result.features]
        has_state_feature = any("state" in n or "turn" in n or "on" in n for n in feature_names)
        assert has_state_feature, f"Expected state-related feature, got: {feature_names}"

    def test_suggest_adaptations(self):
        """LLM suggests adaptations for a change requirement."""
        tree = self._make_hooverlang_tree()
        llm = LLMClient()
        analyzer = FeatureAnalyzer(llm=llm)

        analysis = analyzer.analyze_with_llm(
            source=DEFAULT_PROGRAM,
            parse_tree=tree,
            language_description="State machine for vacuum cleaner with on/off states.",
        )

        suggestions = analyzer.suggest_adaptations(
            analysis=analysis,
            requirement="Add a stand-by state that activates when the vacuum cleaner "
            "has been idle for too long. The turn-on action should also reset "
            "an inactivity timer.",
            available_slices=["sm.state", "sm.state_standby", "sm.event", "sm.transition"],
        )

        assert len(suggestions) > 0
        # Should suggest adapting state-related micro-language
        assert any(s.adaptation_type in ("system-wide", "localised") for s in suggestions)
        assert any(s.confidence > 0 for s in suggestions)
