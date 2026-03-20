"""μDA operation dataclasses — the IR between parser and executor."""

from __future__ import annotations

from dataclasses import dataclass, field


# --- Context Definitions ---

@dataclass
class SliceBinding:
    """slice old: qualified.name;"""
    names: list[str]
    qualified_name: str
    endemic: bool = False


@dataclass
class NonterminalBinding:
    """nt for1,_,_ : Rule from module Mod;"""
    names: list[str]
    rule_name: str
    module_name: str


@dataclass
class ActionBinding:
    """action X : NT from module Mod role R;"""
    name: str
    nonterminal: str
    module_name: str
    role: str


# --- System-Wide Operations ---

@dataclass
class ReplaceSlice:
    """replace slice old with new;"""
    old_name: str
    new_name: str


@dataclass
class RedoRole:
    """redo [from node] [role name];"""
    from_node: str | None = None
    role: str | None = None


# --- Localised Operations ---

@dataclass
class AddAction:
    """add action X [to Y] in role R;"""
    action_name: str
    role: str
    target_name: str | None = None


@dataclass
class RemoveAction:
    """remove action X [from Y] in role R;"""
    action_name: str
    role: str
    target_name: str | None = None


@dataclass
class SetSpecialized:
    """set specialized action for X to Y in role R;"""
    nonterminal_name: str
    action_name: str
    role: str


# --- Matching Expressions ---

@dataclass
class NodeMatch:
    """id[cond1][cond2]..."""
    name: str
    conditions: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class ParentPathMatch:
    """child < parent [| filter]"""
    child: NodeMatch
    parent: NodeMatch
    filter_name: str | None = None


@dataclass
class ReachablePathMatch:
    """descendant << ancestor [| filter]"""
    descendant: NodeMatch
    ancestor: NodeMatch
    filter_name: str | None = None


MatchExpr = NodeMatch | ParentPathMatch | ReachablePathMatch
Manipulation = AddAction | RemoveAction | SetSpecialized
ContextDef = SliceBinding | NonterminalBinding | ActionBinding


# --- Clauses ---

@dataclass
class WhenClause:
    match_expr: MatchExpr
    manipulations: list[Manipulation]


@dataclass
class SystemWideClause:
    operations: list[ReplaceSlice | RedoRole]


# --- Top-Level ---

@dataclass
class AdaptationScript:
    """Complete parsed μDA script."""
    context: list[ContextDef]
    clauses: list[WhenClause | SystemWideClause]


@dataclass
class AdaptationResult:
    """Result of executing an adaptation."""
    success: bool
    operations_applied: list[str]
    errors: list[str] = field(default_factory=list)
