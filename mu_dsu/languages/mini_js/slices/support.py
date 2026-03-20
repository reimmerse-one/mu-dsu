"""Support slice — terminals for MiniJS."""

from mu_dsu.core.slice import LanguageSlice, SyntaxDefinition


def support_slice() -> LanguageSlice:
    return LanguageSlice(
        name="viewer.support",
        syntax=SyntaxDefinition(
            rules='_placeholder_support: "NEVERMATCHES_SUPPORT"',
            terminals=(
                'IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/\n'
                'STRING: /\\"[^\\"]*\\"/ | /\'[^\']*\'/\n'
                "%import common.NUMBER\n"
                "%import common.WS\n"
                "%ignore WS\n"
                "%ignore /\\n/\n"
            ),
        ),
    )
