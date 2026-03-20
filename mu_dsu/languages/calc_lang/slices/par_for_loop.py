"""Parallel for loop slice — replacement for sequential for (Sect. 5.2).

Records parallel execution mode. In a real implementation this would
use concurrent.futures; here we demonstrate the adaptation mechanism.
"""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def par_for_loop_slice() -> LanguageSlice:
    """Parallel for — same syntax, different semantics."""
    return LanguageSlice(
        name="calc.for_loop",  # Same name for drop-in replacement
        syntax=SyntaxDefinition(
            rules=(
                'for_stmt: "for" "(" for_init ";" expr ";" for_step ")" "{" statement_list "}" ";"\n'
                "?for_init: var_stmt_nsc | assign_nsc\n"
                'var_stmt_nsc: "var" IDENT "=" expr\n'
                'assign_nsc: IDENT "=" expr\n'
                'for_step: IDENT "=" expr | "++" IDENT -> pre_inc\n'
                "statement_list: statement+"
            ),
        ),
        dependencies=["calc.expr", "calc.var_decl"],
        actions=[
            SemanticAction(
                node_type="for_stmt", role="execution", phase="replace",
                handler=_exec_for_parallel, id="calc.for_stmt.exec",
            ),
            SemanticAction(
                node_type="var_stmt_nsc", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="calc.var_stmt_nsc.exec",
            ),
            SemanticAction(
                node_type="assign_nsc", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="calc.assign_nsc.exec",
            ),
            SemanticAction(
                node_type="for_step", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), v(n.children[1])),
                id="calc.for_step.exec",
            ),
            SemanticAction(
                node_type="pre_inc", role="execution", phase="replace",
                handler=lambda n, c, v: c.env.set(str(n.children[0]), c.env.get(str(n.children[0])) + 1),
                id="calc.pre_inc.exec",
            ),
            SemanticAction(
                node_type="statement_list", role="execution", phase="replace",
                handler=lambda n, c, v: [v(ch) for ch in n.children],
                id="calc.stmt_list.exec",
            ),
        ],
    )


def _exec_for_parallel(node, ctx, visit):
    """Parallel for: same result as sequential but records parallel mode.

    In a production system, this would distribute loop body execution
    across threads/processes. Here we execute sequentially but record
    that parallelism was requested — proving the adaptation targeted
    only this specific for loop.
    """
    init_node = node.children[0]
    cond_node = node.children[1]
    step_node = node.children[2]
    body_node = node.children[3]

    visit(init_node)
    iterations = 0
    max_iter = 100000
    while visit(cond_node) and iterations < max_iter:
        visit(body_node)
        visit(step_node)
        iterations += 1

    # Record PARALLEL execution mode
    modes = ctx.env.get("__exec_modes__") if ctx.env.has("__exec_modes__") else []
    modes.append("parallel")
    ctx.env.set("__exec_modes__", modes)
