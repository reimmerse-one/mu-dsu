"""Action slice — state initialization actions (func_call, assignment, named actions)."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def action_slice() -> LanguageSlice:
    return LanguageSlice(
        name="sm.action",
        syntax=SyntaxDefinition(
            rules=(
                'action_list: action (";" action)*\n'
                "?action: assignment\n"
                "    | func_call\n"
                "    | IDENT -> named_action\n"
                'func_call: IDENT "." IDENT "(" ")"\n'
                'assignment: IDENT "<-" expr'
            ),
        ),
        dependencies=["sm.expr"],
        actions=[
            SemanticAction(
                node_type="action_list", role="execution", phase="replace",
                handler=_exec_action_list,
                id="sm.action_list.exec",
            ),
            SemanticAction(
                node_type="named_action", role="execution", phase="replace",
                handler=lambda node, ctx, visit: str(node.children[0]),
                id="sm.named_action.exec",
            ),
            SemanticAction(
                node_type="func_call", role="execution", phase="replace",
                handler=_exec_func_call,
                id="sm.func_call.exec",
            ),
            SemanticAction(
                node_type="assignment", role="execution", phase="replace",
                handler=_exec_assignment,
                id="sm.assignment.exec",
            ),
        ],
    )


def _exec_action_list(node, ctx, visit):
    """Execute all actions in the list, return list of results."""
    results = []
    for child in node.children:
        results.append(visit(child))
    return results


def _exec_func_call(node, ctx, visit):
    """Call obj.method() — looked up in env globals."""
    obj_name = str(node.children[0])
    method_name = str(node.children[1])
    key = f"{obj_name}.{method_name}"
    if ctx.env.has(key):
        fn = ctx.env.get(key)
        return fn()
    return None


def _exec_assignment(node, ctx, visit):
    """Execute `var <- expr`."""
    name = str(node.children[0])
    value = visit(node.children[1])
    ctx.env.set(name, value)
    return value
