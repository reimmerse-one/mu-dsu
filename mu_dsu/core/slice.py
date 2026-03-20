"""Language slice — the atomic unit of language composition.

Maps to Neverlang's 'slice' concept: a bundle of grammar fragment + semantic actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from lark import Token, Tree

# Type alias for the visit callback passed to replace/after handlers
VisitFn = Callable[[Tree | Token], Any]

VALID_PHASES: frozenset[str] = frozenset({"before", "after", "replace"})


@dataclass
class SyntaxDefinition:
    """Grammar fragment in Lark EBNF notation."""

    rules: str
    terminals: str = ""
    priority: int = 0


@dataclass
class SemanticAction:
    """Action executed when an AST node is visited.

    Handler signatures by phase:
        before:  (node: Tree, ctx: Context) -> None
        replace: (node: Tree, ctx: Context, visit: VisitFn) -> Any
        after:   (node: Tree, ctx: Context, visit: VisitFn, result: Any) -> Any
    """

    node_type: str
    role: str
    phase: str
    handler: Callable[..., Any]
    id: str = ""

    def __post_init__(self) -> None:
        if self.phase not in VALID_PHASES:
            raise ValueError(
                f"Invalid phase {self.phase!r}, must be one of {sorted(VALID_PHASES)}"
            )
        if not self.id:
            self.id = f"{self.node_type}.{self.role}.{self.phase}"


@dataclass
class LanguageSlice:
    """The atomic unit of language composition.

    Bundles a grammar fragment (SyntaxDefinition) with semantic actions.
    Multiple slices are composed by GrammarComposer to form a complete language.
    """

    name: str
    syntax: SyntaxDefinition
    actions: list[SemanticAction] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Check that the slice is well-formed."""
        if not self.name:
            raise ValueError("Slice name must not be empty")
        if not self.syntax.rules.strip():
            raise ValueError(f"Slice {self.name!r}: syntax rules must not be empty")
