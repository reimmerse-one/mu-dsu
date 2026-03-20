"""Parse tree matching engine for localised adaptations.

Implements the matching expressions from Table 1:
- NodeMatch: match nodes by type and conditions
- ParentPathMatch (<): child is a direct child of parent
- ReachablePathMatch (<<): descendant is reachable from ancestor
"""

from __future__ import annotations

from lark import Token, Tree

from mu_dsu.adaptation.context import ResolvedContext
from mu_dsu.adaptation.operations import (
    MatchExpr,
    NodeMatch,
    ParentPathMatch,
    ReachablePathMatch,
)


class ParseTreeMatcher:
    """Matches parse tree nodes against μDA matching expressions."""

    def match(
        self,
        expr: MatchExpr,
        parse_tree: Tree,
        ctx: ResolvedContext,
    ) -> list[Tree]:
        """Find all nodes matching the expression."""
        if isinstance(expr, NodeMatch):
            return self._find_matching_nodes(parse_tree, expr, ctx)
        elif isinstance(expr, ParentPathMatch):
            return self._match_parent_path(parse_tree, expr, ctx)
        elif isinstance(expr, ReachablePathMatch):
            return self._match_reachable_path(parse_tree, expr, ctx)
        return []

    def _find_matching_nodes(
        self, tree: Tree, match: NodeMatch, ctx: ResolvedContext
    ) -> list[Tree]:
        """Collect all nodes matching a NodeMatch."""
        node_type = ctx.nonterminals.get(match.name, match.name)
        results: list[Tree] = []
        self._walk(tree, node_type, match.conditions, results)
        return results

    def _walk(
        self,
        node: Tree | Token,
        node_type: str,
        conditions: list[tuple[str, str]],
        results: list[Tree],
    ) -> None:
        if isinstance(node, Token):
            return
        if node.data == node_type and self._check_conditions(node, conditions):
            results.append(node)
        for child in node.children:
            if isinstance(child, Tree):
                self._walk(child, node_type, conditions, results)

    def _check_conditions(self, node: Tree, conditions: list[tuple[str, str]]) -> bool:
        """Check attribute conditions against a node."""
        for attr, value in conditions:
            # Strip quotes from string values
            clean_value = value.strip('"').strip("'")
            if attr == "name" or attr == "data":
                if node.data != clean_value:
                    return False
            elif attr == "child0":
                # Check first child's string value
                if not node.children or str(node.children[0]) != clean_value:
                    return False
            else:
                # Generic: check if any child token matches
                found = False
                for child in node.children:
                    if isinstance(child, Token) and str(child) == clean_value:
                        found = True
                        break
                if not found:
                    return False
        return True

    def _match_parent_path(
        self, tree: Tree, expr: ParentPathMatch, ctx: ResolvedContext
    ) -> list[Tree]:
        """child < parent: find child nodes that are direct children of parent nodes."""
        child_type = ctx.nonterminals.get(expr.child.name, expr.child.name)
        parent_type = ctx.nonterminals.get(expr.parent.name, expr.parent.name)

        results: list[Tree] = []
        self._walk_parent_path(tree, child_type, parent_type,
                               expr.child.conditions, expr.parent.conditions,
                               expr.filter_name, results)
        return results

    def _walk_parent_path(
        self,
        node: Tree | Token,
        child_type: str,
        parent_type: str,
        child_conds: list[tuple[str, str]],
        parent_conds: list[tuple[str, str]],
        filter_name: str | None,
        results: list[Tree],
    ) -> None:
        if isinstance(node, Token):
            return
        if node.data == parent_type and self._check_conditions(node, parent_conds):
            # Found a parent — check its direct children
            for child in node.children:
                if isinstance(child, Tree) and child.data == child_type:
                    if self._check_conditions(child, child_conds):
                        # Filter selects which node to return
                        if filter_name == parent_type or filter_name is None:
                            results.append(child)
                        else:
                            results.append(child)
        for child in node.children:
            if isinstance(child, Tree):
                self._walk_parent_path(child, child_type, parent_type,
                                       child_conds, parent_conds, filter_name, results)

    def _match_reachable_path(
        self, tree: Tree, expr: ReachablePathMatch, ctx: ResolvedContext
    ) -> list[Tree]:
        """from_node << to_node: find to_node reachable from from_node.

        Paper Table 1: 'id1 << id2' matches a path where id2 can be reached from id1.
        So id1 (descendant field) is the container/ancestor, id2 (ancestor field)
        is the target/descendant that can be reached.
        """
        from_type = ctx.nonterminals.get(expr.descendant.name, expr.descendant.name)
        to_type = ctx.nonterminals.get(expr.ancestor.name, expr.ancestor.name)

        # Find all "from" nodes (containers)
        containers: list[Tree] = []
        self._walk(tree, from_type, expr.descendant.conditions, containers)

        results: list[Tree] = []
        for container in containers:
            # Find "to" nodes within the container's subtree
            targets: list[Tree] = []
            self._walk(container, to_type, expr.ancestor.conditions, targets)
            for target in targets:
                if target is not container:  # Don't match self
                    # Filter: determines which node to return as the match result
                    if expr.filter_name and expr.filter_name == expr.ancestor.name:
                        # filter=to_name -> return the target (inner/reachable node)
                        results.append(target)
                    elif expr.filter_name and expr.filter_name == expr.descendant.name:
                        # filter=from_name -> return the container
                        if container not in results:
                            results.append(container)
                    else:
                        results.append(target)

        return results
