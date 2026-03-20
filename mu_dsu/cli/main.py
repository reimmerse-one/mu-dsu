"""μ-DSU CLI — command-line interface for the framework."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from mu_dsu.cli.registry import LanguageRegistry


def _get_registry() -> LanguageRegistry:
    return LanguageRegistry()


def _resolve_language(lang: str | None, program: str | None, registry: LanguageRegistry):
    """Resolve language by name or file extension."""
    if lang:
        return registry.get(lang)
    if program:
        ext = Path(program).suffix
        entry = registry.find_by_extension(ext)
        if entry:
            return entry
    raise click.UsageError("Specify --lang or use a recognized file extension")


@click.group()
@click.version_option(package_name="mu-dsu")
def cli():
    """μ-DSU: Micro-language based Dynamic Software Updating."""


# ── run ──────────────────────────────────────────────────────────────

@cli.command()
@click.argument("program", type=click.Path(exists=True))
@click.option("--lang", "-l", help="Language name (hooverlang, minijs, calclang)")
def run(program: str, lang: str | None):
    """Run a program on a registered language."""
    registry = _get_registry()
    entry = _resolve_language(lang, program, registry)
    interp = entry.create_interpreter()
    source = Path(program).read_text()

    result = interp.run(source)
    if result is not None:
        click.echo(result)


# ── adapt ────────────────────────────────────────────────────────────

@cli.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--target", "-t", required=True, type=click.Path(exists=True),
              help="Program to adapt")
@click.option("--lang", "-l", required=True, help="Language name")
@click.option("--slice-registry", "-s", multiple=True,
              help="Slice registry entries: name=module.path:factory_func")
def adapt(script: str, target: str, lang: str, slice_registry: tuple[str, ...]):
    """Apply a μDA adaptation script to a program."""
    import importlib
    from mu_dsu.adaptation.adapter import MicroLanguageAdapter

    registry = _get_registry()
    entry = registry.get(lang)
    interp = entry.create_interpreter()
    source = Path(target).read_text()
    interp.run(source)

    # Build slice registry from --slice-registry args
    sr = {}
    for spec in slice_registry:
        name, path = spec.split("=", 1)
        mod_path, func_name = path.rsplit(":", 1)
        mod = importlib.import_module(mod_path)
        sr[name] = getattr(mod, func_name)()

    adapter = MicroLanguageAdapter(slice_registry=sr)
    mda_script = Path(script).read_text()
    result = adapter.adapt(mda_script, interp)

    if result.success:
        click.secho(f"Adaptation successful: {len(result.operations_applied)} operations", fg="green")
        for op in result.operations_applied:
            click.echo(f"  {op}")
    else:
        click.secho("Adaptation failed:", fg="red")
        for err in result.errors:
            click.echo(f"  {err}")
        sys.exit(1)


# ── analyze ──────────────────────────────────────────────────────────

@cli.command()
@click.argument("program", type=click.Path(exists=True))
@click.option("--lang", "-l", required=True, help="Language name")
@click.option("--llm", is_flag=True, help="Use LLM-assisted analysis")
@click.option("--description", "-d", default="", help="Language description for LLM context")
def analyze(program: str, lang: str, llm: bool, description: str):
    """Analyze application features and micro-languages."""
    from mu_dsu.analysis.feature_analyzer import FeatureAnalyzer

    registry = _get_registry()
    entry = registry.get(lang)
    interp = entry.create_interpreter()
    source = Path(program).read_text()
    tree = interp.load(source)

    if llm:
        from mu_dsu.analysis.llm_client import LLMClient
        client = LLMClient()
        analyzer = FeatureAnalyzer(llm=client)
        result = analyzer.analyze_with_llm(source, tree, description)
    else:
        analyzer = FeatureAnalyzer()
        result = analyzer.analyze_ast(tree)

    click.secho(f"\nFeatures ({len(result.features)}):", bold=True)
    for f in result.features:
        click.echo(f"  {f.name}: {f.description or ', '.join(f.node_types)}")

    click.secho(f"\nMicro-languages ({len(result.micro_languages)}):", bold=True)
    for ml in result.micro_languages:
        click.echo(f"  {ml.name}: {ml.language_features}")
        if ml.overlaps_with:
            click.echo(f"    overlaps: {ml.overlaps_with}")


# ── suggest ──────────────────────────────────────────────────────────

@cli.command()
@click.argument("requirement")
@click.option("--program", "-p", type=click.Path(exists=True), help="Program to analyze")
@click.option("--lang", "-l", required=True, help="Language name")
@click.option("--slices", help="Comma-separated available slice names")
def suggest(requirement: str, program: str | None, lang: str, slices: str | None):
    """Suggest μDA adaptations from a natural language requirement."""
    from mu_dsu.analysis.feature_analyzer import FeatureAnalyzer
    from mu_dsu.analysis.llm_client import LLMClient

    registry = _get_registry()
    entry = registry.get(lang)
    interp = entry.create_interpreter()

    if program:
        source = Path(program).read_text()
        tree = interp.load(source)
    else:
        click.echo("Warning: no program provided, using empty analysis", err=True)
        tree = interp.load("")

    client = LLMClient()
    analyzer = FeatureAnalyzer(llm=client)
    analysis = analyzer.analyze_with_llm(
        source=Path(program).read_text() if program else "",
        parse_tree=tree,
    )

    available = slices.split(",") if slices else None
    suggestions = analyzer.suggest_adaptations(analysis, requirement, available)

    click.secho(f"\nSuggestions ({len(suggestions)}):", bold=True)
    for s in suggestions:
        click.echo(f"\n  {s.micro_language} ({s.adaptation_type}, confidence={s.confidence:.0%})")
        click.echo(f"  {s.description}")
        if s.target_slices:
            click.echo(f"  target: {', '.join(s.target_slices)}")
        if s.mu_da_script:
            click.secho("  μDA script:", dim=True)
            for line in s.mu_da_script.strip().split("\n"):
                click.echo(f"    {line}")


# ── lang ─────────────────────────────────────────────────────────────

@cli.group()
def lang():
    """Manage registered languages."""


@lang.command("list")
def lang_list():
    """List registered languages."""
    registry = _get_registry()
    for entry in registry.list_all():
        exts = ", ".join(entry.extensions) if entry.extensions else "-"
        click.echo(f"  {entry.name:15s} {exts:20s} {entry.description}")


@lang.command("info")
@click.argument("name")
def lang_info(name: str):
    """Show details about a language."""
    registry = _get_registry()
    entry = registry.get(name)
    composer, actions = entry.compose()

    click.secho(f"\n{entry.name}", bold=True)
    click.echo(f"  {entry.description}")
    click.echo(f"  Extensions: {', '.join(entry.extensions)}")
    click.echo(f"  Compose: {entry.compose_path}")
    click.secho(f"\n  Slices ({len(composer.slices)}):", bold=True)
    for name, sl in composer.slices.items():
        deps = f" (depends: {', '.join(sl.dependencies)})" if sl.dependencies else ""
        click.echo(f"    {name}{deps}")
        click.echo(f"      actions: {len(sl.actions)}")


# ── parse ────────────────────────────────────────────────────────────

@cli.command()
@click.argument("program", type=click.Path(exists=True))
@click.option("--lang", "-l", required=True, help="Language name")
def parse(program: str, lang: str):
    """Parse a program and print the AST."""
    registry = _get_registry()
    entry = registry.get(lang)
    interp = entry.create_interpreter()
    source = Path(program).read_text()
    tree = interp.load(source)
    click.echo(tree.pretty())


if __name__ == "__main__":
    cli()
