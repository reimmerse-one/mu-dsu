"""Support slice — terminals for CalcLang."""

from mu_dsu.core.slice import LanguageSlice, SyntaxDefinition


def support_slice() -> LanguageSlice:
    return LanguageSlice(
        name="calc.support",
        syntax=SyntaxDefinition(
            rules='_placeholder_calc: "NEVERMATCHES_CALC"',
            terminals=(
                'IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/\n'
                "%import common.NUMBER\n"
                "%import common.DECIMAL\n"
                "%import common.WS\n"
                "%ignore WS\n"
                "%ignore /\\n/\n"
            ),
        ),
    )
