"""Types for feature analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApplicationFeature:
    """An identifiable piece of application functionality.

    From the paper (Sect. 2.2): a software application can be described
    in terms of its application features.
    """
    name: str
    description: str
    node_types: list[str] = field(default_factory=list)  # AST node types involved
    code_summary: str = ""


@dataclass
class MicroLanguage:
    """The set of language features involved in implementing
    a specific application feature (Definition from Sect. 2.2).
    """
    name: str
    application_feature: ApplicationFeature
    language_features: set[str] = field(default_factory=set)
    slices: list[str] = field(default_factory=list)
    overlaps_with: list[str] = field(default_factory=list)


@dataclass
class AdaptationSuggestion:
    """A suggested adaptation for a micro-language."""
    micro_language: str
    description: str
    adaptation_type: str  # "system-wide" or "localised"
    target_slices: list[str] = field(default_factory=list)
    mu_da_script: str = ""
    confidence: float = 0.0


@dataclass
class AnalysisResult:
    """Complete result of feature analysis."""
    features: list[ApplicationFeature]
    micro_languages: list[MicroLanguage]
    raw_llm_response: str = ""
