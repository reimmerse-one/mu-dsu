"""μDA DSL grammar in Lark EBNF.

Based on Table 1 of the paper, refined for Lark parsing.
"""

MU_DA_GRAMMAR = r"""
    start: context_section clause+

    // --- Context ---
    context_section: "context" "{" context_def+ "}"
    context_def: slice_def | nt_def | action_def

    slice_def: ENDEMIC? "slice" name_list ":" QUALIFIED_NAME ";"
    nt_def: ("nt" | "production") name_list ":" NAME "from" "module" QUALIFIED_NAME ";"
    action_def: "action" NAME ":" NAME "from" "module" QUALIFIED_NAME "role" NAME ";"

    name_list: NAME ("," NAME)*
    ENDEMIC: "endemic"

    // --- Clauses ---
    ?clause: system_wide_clause | when_clause

    // --- System-Wide ---
    system_wide_clause: "system-wide" "{" sys_op+ "}"
    ?sys_op: replace_slice | redo_role

    replace_slice: "replace" "slice" NAME "with" NAME ";"
    redo_role: "redo" redo_from? redo_role_name? ";"
    redo_from: "from" NAME
    redo_role_name: "role" NAME

    // --- Localised ---
    when_clause: "when" match_expr "occurs" "{" manipulation+ "}"

    // --- Matching Expressions ---
    ?match_expr: reachable_path_match | parent_path_match | node_match

    node_match: NAME condition*
    parent_path_match: node_match "<" node_match filter_op?
    reachable_path_match: node_match "<<" node_match filter_op?
    filter_op: "|" NAME

    condition: "[" NAME "=" VALUE "]"

    // --- Manipulations ---
    ?manipulation: add_action | remove_action | set_specialized

    add_action: "add" "action" NAME add_target? "in" "role" NAME ";"
    add_target: "to" NAME

    remove_action: "remove" "action" NAME remove_target? "in" "role" NAME ";"
    remove_target: "from" NAME

    set_specialized: "set" "specialized" "action" "for" NAME "to" NAME "in" "role" NAME ";"

    // --- Terminals ---
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    QUALIFIED_NAME: /[a-zA-Z_][a-zA-Z0-9_.]+/
    VALUE: ESCAPED_STRING | INT | "true" | "false"

    %import common.ESCAPED_STRING
    %import common.INT
    %import common.WS
    %ignore WS
    %ignore /\/\/[^\n]*/
"""
