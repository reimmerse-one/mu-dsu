"""LLM-assisted feature analysis — component ⑤ in Fig. 3.

The paper marks automatic identification of application features
and micro-languages as "currently under investigation" (Sect. 3.1).
We close this gap using AST analysis + LLM-assisted reasoning.
"""

from __future__ import annotations

import json
from typing import Any

from lark import Token, Tree

from mu_dsu.analysis.llm_client import LLMClient
from mu_dsu.analysis.types import (
    AdaptationSuggestion,
    AnalysisResult,
    ApplicationFeature,
    MicroLanguage,
)
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter


class FeatureAnalyzer:
    """Identifies application features and derives micro-language definitions.

    Two modes:
    1. AST-only: static analysis of the parse tree (no LLM needed)
    2. LLM-assisted: uses LLM to understand semantics and suggest adaptations
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    # --- AST-based analysis (no LLM) ---

    def analyze_ast(self, parse_tree: Tree) -> AnalysisResult:
        """Pure AST analysis: extract features from tree structure."""
        node_types = self._collect_node_types(parse_tree)
        subtrees = self._extract_top_level_subtrees(parse_tree)

        features = []
        for name, subtree in subtrees:
            types_used = self._collect_node_types(subtree)
            features.append(ApplicationFeature(
                name=name,
                description=f"Feature implemented by {subtree.data} subtree",
                node_types=sorted(types_used),
                code_summary=self._summarize_subtree(subtree),
            ))

        micro_langs = self._derive_micro_languages(features)

        return AnalysisResult(
            features=features,
            micro_languages=micro_langs,
        )

    def _collect_node_types(self, tree: Tree) -> set[str]:
        """Collect all unique node types in a subtree."""
        types: set[str] = set()
        self._walk_types(tree, types)
        return types

    def _walk_types(self, node: Tree | Token, types: set[str]) -> None:
        if isinstance(node, Token):
            return
        types.add(node.data)
        for child in node.children:
            if isinstance(child, Tree):
                self._walk_types(child, types)

    def _extract_top_level_subtrees(self, tree: Tree) -> list[tuple[str, Tree]]:
        """Extract named top-level subtrees as candidate features."""
        results: list[tuple[str, Tree]] = []
        for child in tree.children:
            if isinstance(child, Tree):
                name = child.data
                # Use first identifier child as feature name if available
                for c in child.children:
                    if isinstance(c, Token) and c.type == "IDENT":
                        name = f"{child.data}_{c}"
                        break
                results.append((name, child))
        return results

    def _summarize_subtree(self, tree: Tree) -> str:
        """Create a short text summary of a subtree."""
        tokens: list[str] = []
        self._collect_tokens(tree, tokens)
        return " ".join(tokens[:20])

    def _collect_tokens(self, node: Tree | Token, tokens: list[str]) -> None:
        if isinstance(node, Token):
            tokens.append(str(node))
        elif isinstance(node, Tree):
            for child in node.children:
                self._collect_tokens(child, tokens)

    def _derive_micro_languages(
        self, features: list[ApplicationFeature]
    ) -> list[MicroLanguage]:
        """Derive micro-language definitions from identified features."""
        micro_langs: list[MicroLanguage] = []
        all_types_map: dict[str, list[str]] = {}  # type -> list of feature names

        for feat in features:
            for nt in feat.node_types:
                all_types_map.setdefault(nt, []).append(feat.name)

        for feat in features:
            overlaps = set()
            for nt in feat.node_types:
                for other in all_types_map.get(nt, []):
                    if other != feat.name:
                        overlaps.add(other)

            ml = MicroLanguage(
                name=f"μ_{feat.name}",
                application_feature=feat,
                language_features=set(feat.node_types),
                overlaps_with=sorted(overlaps),
            )
            micro_langs.append(ml)

        return micro_langs

    # --- LLM-assisted analysis ---

    def analyze_with_llm(
        self,
        source: str,
        parse_tree: Tree,
        language_description: str = "",
    ) -> AnalysisResult:
        """LLM-assisted analysis: understand features semantically."""
        if self._llm is None:
            raise RuntimeError("LLM client not configured")

        # First get AST-based analysis
        ast_result = self.analyze_ast(parse_tree)

        # Build prompt with context
        tree_summary = parse_tree.pretty()[:2000]
        features_summary = "\n".join(
            f"- {f.name}: node_types={f.node_types}" for f in ast_result.features
        )

        prompt = f"""Analyze this program and identify its application features and micro-languages.

## Context
This is a program written in a domain-specific language.
{f"Language description: {language_description}" if language_description else ""}

## Source code:
```
{source}
```

## Parse tree (abbreviated):
```
{tree_summary}
```

## AST-identified features:
{features_summary}

## Task
For each application feature:
1. Give it a clear name and description
2. List the language features (AST node types) it uses
3. Identify which features overlap (share language features)

Respond as JSON:
{{
  "features": [
    {{
      "name": "feature_name",
      "description": "what this feature does",
      "node_types": ["type1", "type2"],
      "overlaps_with": ["other_feature"]
    }}
  ]
}}"""

        raw_response = self._llm.ask_json(prompt)

        # Parse LLM response
        try:
            data = json.loads(self._clean_json(raw_response))
        except json.JSONDecodeError:
            return AnalysisResult(
                features=ast_result.features,
                micro_languages=ast_result.micro_languages,
                raw_llm_response=raw_response,
            )

        features = []
        for f_data in data.get("features", []):
            features.append(ApplicationFeature(
                name=f_data.get("name", "unknown"),
                description=f_data.get("description", ""),
                node_types=f_data.get("node_types", []),
            ))

        micro_langs = self._derive_micro_languages(features)

        return AnalysisResult(
            features=features,
            micro_languages=micro_langs,
            raw_llm_response=raw_response,
        )

    def suggest_adaptations(
        self,
        analysis: AnalysisResult,
        requirement: str,
        available_slices: list[str] | None = None,
    ) -> list[AdaptationSuggestion]:
        """Suggest μDA adaptations for a change requirement."""
        if self._llm is None:
            raise RuntimeError("LLM client not configured")

        features_desc = "\n".join(
            f"- {ml.name}: language_features={ml.language_features}, "
            f"overlaps_with={ml.overlaps_with}"
            for ml in analysis.micro_languages
        )

        slices_desc = ""
        if available_slices:
            slices_desc = f"\nAvailable slices: {', '.join(available_slices)}"

        prompt = f"""Given these micro-languages and a change requirement, suggest adaptations.

## Micro-languages:
{features_desc}
{slices_desc}

## Change requirement:
{requirement}

## Task
Suggest which micro-languages to adapt and how. For each suggestion:
1. Which micro-language to change
2. Whether the adaptation should be system-wide or localised
3. Which slices to target
4. A μDA script skeleton

Respond as JSON:
{{
  "suggestions": [
    {{
      "micro_language": "μ_name",
      "description": "what to change",
      "adaptation_type": "system-wide",
      "target_slices": ["slice_name"],
      "mu_da_script": "context {{ ... }} system-wide {{ ... }}",
      "confidence": 0.8
    }}
  ]
}}"""

        raw_response = self._llm.ask_json(prompt)

        try:
            data = json.loads(self._clean_json(raw_response))
        except json.JSONDecodeError:
            return []

        suggestions = []
        for s_data in data.get("suggestions", []):
            suggestions.append(AdaptationSuggestion(
                micro_language=s_data.get("micro_language", ""),
                description=s_data.get("description", ""),
                adaptation_type=s_data.get("adaptation_type", "system-wide"),
                target_slices=s_data.get("target_slices", []),
                mu_da_script=s_data.get("mu_da_script", ""),
                confidence=s_data.get("confidence", 0.0),
            ))

        return suggestions

    @staticmethod
    def _clean_json(text: str) -> str:
        """Strip markdown fences if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        return text.strip()
