"""Sequential for loop slice (Listing 7)."""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition


def for_loop_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.for_loop",
        syntax=SyntaxDefinition(
            rules=(
                'for_stmt: "for" "(" for_init ";" expr ";" for_step ")" "{" statement_list "}" ";"\n'
                "?for_init: var_stmt_nsc | assign_nsc\n"
                'var_stmt_nsc: "var" IDENT "=" expr\n'
                "assign_nsc: IDENT \"=\" expr\n"
                'for_step: IDENT "=" expr | "++" IDENT -> pre_inc\n'
                "statement_list: statement+"
            ),
        ),
        dependencies=["calc.expr", "calc.var_decl"],
        actions=[
            SemanticAction(
                node_type="for_stmt", role="execution", phase="replace",
                handler=_exec_for_sequential, id="calc.for_stmt.exec",
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


def _exec_for_sequential(node, ctx, visit):
    """Sequential for: init, while(cond) { body; step }."""
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

    # Record execution mode for testing
    modes = ctx.env.get("__exec_modes__") if ctx.env.has("__exec_modes__") else []
    modes.append("sequential")
    ctx.env.set("__exec_modes__", modes)
