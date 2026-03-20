"""μDA script parser — parses μDA scripts into AdaptationScript dataclasses."""

from __future__ import annotations

from pathlib import Path

import lark
from lark import Token, Transformer, Tree

from mu_dsu.adaptation.mu_da_grammar import MU_DA_GRAMMAR
from mu_dsu.adaptation.operations import (
    ActionBinding,
    AddAction,
    AdaptationScript,
    NonterminalBinding,
    NodeMatch,
    ParentPathMatch,
    ReachablePathMatch,
    RedoRole,
    RemoveAction,
    ReplaceSlice,
    SetSpecialized,
    SliceBinding,
    SystemWideClause,
    WhenClause,
)


class _MuDaTransformer(Transformer):
    """Transforms Lark parse tree into μDA operation dataclasses."""

    def start(self, items):
        context = items[0]
        clauses = items[1:]
        return AdaptationScript(context=context, clauses=clauses)

    def context_section(self, items):
        return list(items)

    def context_def(self, items):
        return items[0]

    def slice_def(self, items):
        endemic = False
        if items and isinstance(items[0], Token) and items[0].type == "ENDEMIC":
            endemic = True
            items = items[1:]
        names = items[0]
        qualified_name = str(items[1])
        return SliceBinding(names=names, qualified_name=qualified_name, endemic=endemic)

    def nt_def(self, items):
        names = items[0]
        rule_name = str(items[1])
        module_name = str(items[2])
        return NonterminalBinding(names=names, rule_name=rule_name, module_name=module_name)

    def action_def(self, items):
        name = str(items[0])
        nonterminal = str(items[1])
        module_name = str(items[2])
        role = str(items[3])
        return ActionBinding(name=name, nonterminal=nonterminal, module_name=module_name, role=role)

    def name_list(self, items):
        return [str(item) for item in items]

    # --- System-wide ---

    def system_wide_clause(self, items):
        return SystemWideClause(operations=list(items))

    def replace_slice(self, items):
        return ReplaceSlice(old_name=str(items[0]), new_name=str(items[1]))

    def redo_role(self, items):
        from_node = None
        role = None
        for item in items:
            if isinstance(item, Tree):
                if item.data == "redo_from":
                    from_node = str(item.children[0])
                elif item.data == "redo_role_name":
                    role = str(item.children[0])
        return RedoRole(from_node=from_node, role=role)

    # --- When clause ---

    def when_clause(self, items):
        match_expr = items[0]
        manipulations = items[1:]
        return WhenClause(match_expr=match_expr, manipulations=list(manipulations))

    # --- Matching ---

    def node_match(self, items):
        name = str(items[0])
        conditions = [(str(c[0]), str(c[1])) for c in items[1:] if isinstance(c, tuple)]
        return NodeMatch(name=name, conditions=conditions)

    def parent_path_match(self, items):
        child = items[0]
        parent = items[1]
        filter_name = None
        if len(items) > 2 and items[2] is not None:
            filter_name = items[2]
        return ParentPathMatch(child=child, parent=parent, filter_name=filter_name)

    def reachable_path_match(self, items):
        descendant = items[0]
        ancestor = items[1]
        filter_name = None
        if len(items) > 2 and items[2] is not None:
            filter_name = items[2]
        return ReachablePathMatch(descendant=descendant, ancestor=ancestor, filter_name=filter_name)

    def filter_op(self, items):
        return str(items[0])

    def condition(self, items):
        return (str(items[0]), str(items[1]))

    # --- Manipulations ---

    def add_action(self, items):
        action_name = str(items[0])
        target_name = None
        role = str(items[-1])
        for item in items[1:-1]:
            if isinstance(item, Tree) and item.data == "add_target":
                target_name = str(item.children[0])
        return AddAction(action_name=action_name, role=role, target_name=target_name)

    def remove_action(self, items):
        action_name = str(items[0])
        target_name = None
        role = str(items[-1])
        for item in items[1:-1]:
            if isinstance(item, Tree) and item.data == "remove_target":
                target_name = str(item.children[0])
        return RemoveAction(action_name=action_name, role=role, target_name=target_name)

    def set_specialized(self, items):
        return SetSpecialized(
            nonterminal_name=str(items[0]),
            action_name=str(items[1]),
            role=str(items[2]),
        )


class MuDaParser:
    """Parses μDA scripts into AdaptationScript dataclasses."""

    def __init__(self) -> None:
        self._parser = lark.Lark(MU_DA_GRAMMAR, parser="earley", ambiguity="resolve")
        self._transformer = _MuDaTransformer()

    def parse(self, script: str) -> AdaptationScript:
        tree = self._parser.parse(script)
        return self._transformer.transform(tree)

    def parse_file(self, path: str | Path) -> AdaptationScript:
        return self.parse(Path(path).read_text())
