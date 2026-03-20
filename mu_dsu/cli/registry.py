"""Language registry — maps language names to compose functions."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Callable

from mu_dsu.core.actions import ActionRegistry
from mu_dsu.core.composer import GrammarComposer
from mu_dsu.core.interpreter import Interpreter


@dataclass
class LanguageEntry:
    name: str
    compose_path: str  # "mu_dsu.languages.state_machine:compose_hooverlang"
    extensions: list[str] = field(default_factory=list)
    description: str = ""

    def compose(self) -> tuple[GrammarComposer, ActionRegistry]:
        module_path, func_name = self.compose_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        fn = getattr(module, func_name)
        return fn()

    def create_interpreter(self) -> Interpreter:
        composer, actions = self.compose()
        return Interpreter(composer, actions)


# Built-in languages
BUILTIN_LANGUAGES: dict[str, LanguageEntry] = {
    "hooverlang": LanguageEntry(
        name="hooverlang",
        compose_path="mu_dsu.languages.state_machine:compose_hooverlang",
        extensions=[".sm", ".hoover"],
        description="State machine language (Cazzola et al. Sections 2.3, 3.2)",
    ),
    "minijs": LanguageEntry(
        name="minijs",
        compose_path="mu_dsu.languages.mini_js:compose_mini_js",
        extensions=[".mjs", ".viewer"],
        description="Simplified JavaScript for HTML viewer (Section 5.1)",
    ),
    "calclang": LanguageEntry(
        name="calclang",
        compose_path="mu_dsu.languages.calc_lang:compose_calclang",
        extensions=[".calc"],
        description="Imperative language for Mandelbrot (Section 5.2)",
    ),
}


class LanguageRegistry:
    """Registry of available languages."""

    def __init__(self) -> None:
        self._languages: dict[str, LanguageEntry] = dict(BUILTIN_LANGUAGES)

    def get(self, name: str) -> LanguageEntry:
        key = name.lower()
        if key not in self._languages:
            raise KeyError(
                f"Language {name!r} not found. Available: {', '.join(self._languages)}"
            )
        return self._languages[key]

    def register(self, entry: LanguageEntry) -> None:
        self._languages[entry.name.lower()] = entry

    def list_all(self) -> list[LanguageEntry]:
        return list(self._languages.values())

    def find_by_extension(self, ext: str) -> LanguageEntry | None:
        if not ext.startswith("."):
            ext = f".{ext}"
        for entry in self._languages.values():
            if ext in entry.extensions:
                return entry
        return None
