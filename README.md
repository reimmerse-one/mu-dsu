# μ-DSU

**Micro-language based Dynamic Software Updating** — a Python reimplementation of the framework described in:

> Cazzola, Chitchyan, Rashid, Shaqiri. *"μ-DSU: A Micro-Language Based Approach to Dynamic Software Updating"*, Computer Languages, Systems & Structures, 2017. [DOI: 10.1016/j.cl.2017.07.003](https://doi.org/10.1016/j.cl.2017.07.003)

Instead of patching application code, μ-DSU evolves the **language interpreter** — changing how specific constructs behave for specific application features, while the application source remains untouched.

## Core Idea

A programming language is composed from **slices** — modular units bundling grammar fragments with semantic actions. A **micro-language** is a logical grouping of slices aligned with a specific application feature. When a feature needs to change, you swap or modify its micro-language's slices at runtime. The application code never changes.

```
┌──────────────────────────────────────────────────────────────┐
│                      μ-DSU Framework                          │
│                                                               │
│  Event Sources          Event Manager         Interpreter     │
│  ┌────────────┐        ┌─────────────┐       ┌────────────┐  │
│  │ Timer      │───┐    │ Event Bus   │       │ Grammar    │  │
│  │ File Watch │───┼──▶ │ (pub/sub,   │──▶ Adapter ──▶│ Composer   │  │
│  │ Runtime    │───┘    │  priority)  │   (μDA DSL)  │ Actions    │  │
│  │ System     │        └─────────────┘       │ Interpreter│  │
│  └────────────┘         pause/resume         └────────────┘  │
│                                                    │          │
│                                              Application      │
│                                           (source unchanged)  │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
pip install -e ".[dev]"
pytest  # 188 tests
```

## Usage

### Build a language from composable slices

```python
from mu_dsu.core import (
    GrammarComposer, ActionRegistry, Interpreter,
    LanguageSlice, SyntaxDefinition, SemanticAction,
)

# Slice 1: numbers
numbers = LanguageSlice(
    name="arithmetic.numbers",
    syntax=SyntaxDefinition(
        rules='start: expr\n?expr: NUMBER -> number',
        terminals="%import common.NUMBER\n%import common.WS\n%ignore WS",
    ),
    actions=[SemanticAction(
        node_type="number", role="execution", phase="replace",
        handler=lambda node, ctx, visit: int(node.children[0]),
    )],
)

# Slice 2: addition
addition = LanguageSlice(
    name="arithmetic.addition",
    syntax=SyntaxDefinition(
        rules='?expr: expr "+" NUMBER -> add',
    ),
    dependencies=["arithmetic.numbers"],
    actions=[SemanticAction(
        node_type="add", role="execution", phase="replace",
        handler=lambda node, ctx, visit: visit(node.children[0]) + int(node.children[1]),
    )],
)

# Compose and run
composer = GrammarComposer()
actions = ActionRegistry()
for sl in [numbers, addition]:
    composer.register(sl)
    actions.load_from_slice(sl)

interp = Interpreter(composer, actions)
result = interp.run("2 + 3")  # => 5
```

### Run the HooverLang state machine

```python
from mu_dsu.languages.state_machine import create_runner
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM

runner = create_runner()
runner._interp.env.set_global("get.click", lambda: True)
runner.load(DEFAULT_PROGRAM)

print(runner.current_state)  # "on"
runner.step()
print(runner.current_state)  # "off"
runner.step()
print(runner.current_state)  # "on"
```

### Adapt at runtime with μDA scripts

```python
from mu_dsu.adaptation import MicroLanguageAdapter
from mu_dsu.core import Interpreter
from mu_dsu.languages.state_machine import compose_hooverlang
from mu_dsu.languages.state_machine.examples.default import DEFAULT_PROGRAM
from mu_dsu.languages.state_machine.slices.state_standby import state_standby_slice

# Build interpreter
composer, actions = compose_hooverlang()
interp = Interpreter(composer, actions)
interp.env.set_global("get.click", lambda: False)
interp.run(DEFAULT_PROGRAM)

# Adapt: replace state slice with standby-aware version
adapter = MicroLanguageAdapter(slice_registry={
    "sm.state_standby": state_standby_slice(),
})

adapter.adapt("""
    context {
        slice old: sm.state;
        slice new: sm.state_standby;
    }
    system-wide {
        replace slice old with new;
        redo role execution;
    }
""", interp)

# Interpreter now uses new semantics — app code unchanged
```

### React to events with the Event Manager

```python
import asyncio
from mu_dsu.events import EventManager, Subscription
from mu_dsu.events.sources import TimerSource, FileWatchSource, RuntimeSource, RuntimeCondition

# Wire event system to interpreter + adapter
mgr = EventManager(interpreter=interp, adapter=adapter)

# Subscribe: when config file changes, apply standby adaptation
mgr.subscribe(Subscription(
    event_pattern="file.changed",
    adaptation_script=standby_script,
))
mgr.register_source(FileWatchSource(paths=["config.cfg"], poll_interval=1.0))

# Or react to runtime conditions (edge-triggered)
mgr.register_source(RuntimeSource(interp, [
    RuntimeCondition(
        name="inactivity",
        check=lambda i: i.env.has("inactive") and i.env.get("inactive"),
        event_type="runtime.inactivity",
    ),
]))

# Run the event loop
asyncio.run(mgr.run(timeout=60))
```

### Analyze features with LLM assistance

```python
from mu_dsu.analysis import FeatureAnalyzer
from mu_dsu.analysis.llm_client import LLMClient

# Analyze a program's features and micro-languages
llm = LLMClient()  # Uses OpenRouter + Gemini Flash (OPENROUTER_API_KEY from .env)
analyzer = FeatureAnalyzer(llm=llm)

result = analyzer.analyze_with_llm(
    source=program_text,
    parse_tree=interp.parse_tree,
    language_description="State machine language for appliance control",
)

for ml in result.micro_languages:
    print(f"{ml.name}: {ml.language_features}")

# Suggest adaptations for a change requirement
suggestions = analyzer.suggest_adaptations(
    analysis=result,
    requirement="Add stand-by mode that activates after inactivity",
    available_slices=["sm.state", "sm.state_standby"],
)
for s in suggestions:
    print(f"{s.description} ({s.adaptation_type}, confidence={s.confidence})")
```

## Architecture

### Core (`mu_dsu/core/`)

| Module | Purpose |
|--------|---------|
| `slice.py` | `LanguageSlice`, `SyntaxDefinition`, `SemanticAction` — the atomic unit of language composition |
| `composer.py` | `GrammarComposer` — merges Lark grammars from slices, handles dependencies, builds parser |
| `actions.py` | `ActionRegistry` — maps (node_type, role) to semantic actions, supports dynamic add/remove/replace |
| `interpreter.py` | Tree-walking interpreter with before/replace/after phase dispatch, pause/resume for adaptation |
| `environment.py` | Variable bindings with lexical scope chain |

### Adaptation (`mu_dsu/adaptation/`)

| Module | Purpose |
|--------|---------|
| `mu_da_grammar.py` | μDA DSL grammar (Lark EBNF), based on Table 1 of the paper |
| `mu_da_parser.py` | Parses μDA scripts into typed operation dataclasses |
| `operations.py` | 19 dataclasses representing μDA operations (SliceBinding, ReplaceSlice, WhenClause, ...) |
| `context.py` | Resolves symbolic names in μDA scripts to concrete slices/actions |
| `matcher.py` | Parse tree matching: node match, parent path (`<`), reachable path (`<<`) |
| `adapter.py` | `MicroLanguageAdapter` — orchestrates parsing, context resolution, and execution |

### Events (`mu_dsu/events/`)

| Module | Purpose |
|--------|---------|
| `types.py` | `Event`, `Subscription`, `EventPriority` — typed events with priority levels |
| `bus.py` | `EventBus` — synchronous pub/sub with glob pattern matching and priority sorting |
| `manager.py` | `EventManager` — async coordinator: sources → bus → adapter → interpreter |
| `sources/timer.py` | `TimerSource` — periodic tick events |
| `sources/file_watch.py` | `FileWatchSource` — file change detection via mtime polling |
| `sources/runtime.py` | `RuntimeSource` — edge-triggered interpreter state monitoring |

### Analysis (`mu_dsu/analysis/`)

| Module | Purpose |
|--------|---------|
| `types.py` | `ApplicationFeature`, `MicroLanguage`, `AdaptationSuggestion`, `AnalysisResult` |
| `llm_client.py` | OpenRouter API client (Gemini Flash via OpenAI SDK) |
| `feature_analyzer.py` | AST-based + LLM-assisted feature identification and adaptation suggestion |

### Languages (`mu_dsu/languages/`)

| Language | Slices | Description |
|----------|--------|-------------|
| HooverLang | 10 | State machine language (Sections 2.3, 3.2). States, events, transitions, counters |
| MiniJS | 6 | Simplified JavaScript for HTML viewer (Section 5.1). Print, set font size/color |
| CalcLang | 7 | Imperative language for Mandelbrot (Section 5.2). For/while loops, arithmetic, arrays |

## μDA DSL Reference

The μDA (micro Dynamic Adaptation) DSL controls how the interpreter adapts at runtime.

### Context

Binds symbolic names to slices, nonterminals, and actions:

```
context {
    slice old: sm.state;                                    // bind slice by qualified name
    slice new: sm.state_standby;
    endemic slice local: sm.local;                          // endemic (scope-limited) slice
    nt x, y : ForStatement from module sm.control;          // bind nonterminals
    action act : state_def from module sm.state role execution;  // bind action
}
```

### System-Wide Adaptation

Affects all uses of a language feature globally:

```
system-wide {
    replace slice old with new;   // swap one slice for another
    redo role execution;          // re-execute semantic actions from root
}
```

### Localised Adaptation

Affects only specific parse tree nodes:

```
// Match by node type
when state_def occurs {
    add action logAct in role execution;
}

// Match by parent path (direct child)
when child < parent occurs {
    remove action oldAct from target in role execution;
}

// Match by reachable path (any ancestor) with filter
when inner_for << outer_for | outer_for occurs {
    set specialized action for outer_for to parAct in role execution;
}
```

## Project Structure

```
mu_dsu/
├── core/                          # Framework foundation
│   ├── slice.py                   # LanguageSlice, SyntaxDefinition, SemanticAction
│   ├── composer.py                # Grammar composition from slices
│   ├── actions.py                 # Semantic action registry
│   ├── interpreter.py             # Tree-walking interpreter with pause/resume
│   └── environment.py             # Runtime variable bindings
├── adaptation/                    # μDA DSL and adaptation engine
│   ├── mu_da_grammar.py           # μDA Lark grammar
│   ├── mu_da_parser.py            # μDA parser + transformer
│   ├── operations.py              # Typed operation dataclasses
│   ├── context.py                 # Context resolution
│   ├── matcher.py                 # Parse tree matching
│   └── adapter.py                 # MicroLanguageAdapter
├── events/                        # Async event-driven coordination
│   ├── types.py                   # Event, Subscription, EventPriority
│   ├── bus.py                     # EventBus (pub/sub, glob matching)
│   ├── manager.py                 # EventManager (async coordinator)
│   └── sources/                   # Event sources
│       ├── timer.py               # Periodic timer events
│       ├── file_watch.py          # File change detection
│       └── runtime.py             # Interpreter state monitoring
├── languages/
│   └── state_machine/             # HooverLang
│       ├── slices/                # 10 composable slices
│       ├── examples/              # Default + standby programs
│       └── runner.py              # Step-driven SM executor
tests/                             # 283 tests
├── test_core/                     # 61 tests — slices, composer, actions, interpreter
├── test_adaptation/               # 19 tests — μDA parser, context, matcher, adapter
├── test_events/                   # 35 tests — bus, manager, sources, integration
└── test_languages/                # 24 tests — HooverLang grammar, execution, standby
```

## Beyond the Paper: LLM-Assisted Feature Analysis

The original paper was published in 2017 — well before the LLM revolution. In Section 3.1 (component 5, Fig. 3), the authors explicitly note that automatic identification of application features and their associated micro-languages is *"currently under investigation"*. This was the main open gap in the μ-DSU architecture: a human had to manually define which parts of the code constitute which application feature, and which language features (slices) each one uses.

We close this gap by leveraging modern LLMs.

### What the paper left open

The μ-DSU adaptation pipeline requires knowing:
1. **Application features** — what logical features the program implements (e.g., "turning on", "calculating columns")
2. **Micro-language mappings** — which language features (AST node types, slices) each application feature uses
3. **Overlap analysis** — which micro-languages share language features, determining whether an adaptation should be system-wide or localised

In 2017, all of this had to be done manually by the developer. The paper proposed an automated "analysis" component but provided no implementation.

### What we added

**`mu_dsu/analysis/`** implements a two-tier analysis system:

**Tier 1 — AST-based analysis (no LLM, deterministic):**
- Walks the parse tree, extracts top-level subtrees as candidate application features
- Collects the set of node types (language features) each feature uses
- Computes overlap between features to determine micro-language boundaries
- Works offline, zero cost, useful as a baseline

**Tier 2 — LLM-assisted analysis (OpenRouter / Gemini Flash):**
- Sends the parse tree structure + source code to the LLM with a domain-aware prompt
- The LLM identifies features *semantically* — understanding that `states on = turn-on` implements a "turning on" feature, not just a "state_def node"
- Returns structured JSON: named features, descriptions, node type mappings, overlaps
- **Adaptation suggestions** — given a natural language requirement (e.g., *"add stand-by mode when idle"*), the LLM maps it to specific micro-languages and proposes whether the change should be system-wide or localised, which slices to target, and generates a μDA script skeleton

### Example: from requirement to μDA script

```python
# Human describes the change in natural language
suggestions = analyzer.suggest_adaptations(
    analysis=result,
    requirement="Add stand-by mode that activates after inactivity. "
                "When turning on, reset an inactivity timer.",
    available_slices=["sm.state", "sm.state_standby", "sm.transition"],
)

# LLM returns:
# - micro_language: "μ_turning_on"
# - adaptation_type: "system-wide"
# - target_slices: ["sm.state"]
# - mu_da_script: "context { slice old: sm.state; slice new: sm.state_standby; } ..."
# - confidence: 0.85
```

This completes the loop that the paper envisioned but couldn't implement in 2017: a developer describes *what* should change in plain language, the LLM identifies *where* in the micro-language structure the change maps to, and the μDA DSL engine executes it against the running interpreter — all without modifying the application source code.

### Why this matters

The original μ-DSU paper proposed a powerful architecture for evolving software at the language level. But it had a practical bottleneck: someone had to manually analyze the program, identify features, and write μDA scripts. With LLMs, this bottleneck is removed. The analysis component can now:

- **Onboard** — analyze an unfamiliar program and map its feature structure automatically
- **Advise** — suggest what kind of adaptation (system-wide vs localised) fits a given change
- **Generate** — produce μDA script skeletons that the developer can review and refine
- **Explain** — describe in natural language what each micro-language controls and how features overlap

This transforms μ-DSU from a framework that requires deep language engineering expertise into one that can be used by developers who understand their *domain* but not necessarily the internal structure of the language interpreter.

## Differences from the Original

| Aspect | Original (2017) | This Implementation |
|--------|----------------|---------------------|
| Language | Java | Python 3.12+ |
| Framework | Neverlang | Custom, built on Lark |
| Grammar format | Neverlang modules | Lark EBNF |
| Event manager | Bash scripts | Async event bus with typed events, priority queue, pub/sub |
| Feature analysis | "Under investigation" | AST analysis + LLM-assisted (Gemini Flash) |
| Parser rebuild | Neverlang hot-swap | Lark parser rebuild on slice change |
| Adaptation DSL | μDA (undocumented impl) | μDA reimplemented as self-hosted DSL with Lark parser |
| Demonstrative studies | 2 (HTML viewer, Mandelbrot) | 3 (+ vacuum cleaner as standalone study) |
| Languages built | 1 (Neverlang.JS subset) | 3 (HooverLang, MiniJS, CalcLang) |

## Paper Conformance

Full conformance report with I/O tables, exact-match checks, and known deviations: **[`docs/PAPER_CONFORMANCE.md`](docs/PAPER_CONFORMANCE.md)**

88 verification tests across three levels, all passing:

| Test suite | What it proves | Tests |
|---|---|---|
| [`tests/test_paper_io.py`](tests/test_paper_io.py) | Same inputs → same outputs as paper describes | 15 |
| [`tests/test_paper_exact_match.py`](tests/test_paper_exact_match.py) | Specific values from paper reproduced exactly | 19 |
| [`tests/test_paper_conformance.py`](tests/test_paper_conformance.py) | Architectural and behavioral properties hold | 54 |

**Important caveat:** verified against the paper's text, not the original code (never published). See the [full report](docs/PAPER_CONFORMANCE.md) for known deviations.

### Known deviations from the original

| Area | Original (Neverlang/Java) | Our interpretation |
|---|---|---|
| Slice count | 13 slices for HooverLang | 10 slices (Lark's `+` handles lists natively, no need for separate StateLst/EventList/TransList slices) |
| Grammar composition | Neverlang merges grammar fragments at the framework level | Lark grammar string concatenation + rule merging with `\|` |
| Parser hot-swap | Neverlang modifies parser in-place without regeneration | Lark requires parser rebuild on slice change (cached, only rebuilt when slices actually change) |
| `production` context binding | Used in Listing 8 for labelled productions | `production` is accepted as a grammar-level synonym for `nt` — both map names to node types and resolve identically |
| Event manager | Bash `while true; do ... done` loop (Listing 6a) | Async `EventManager` with `EventBus`, typed subscriptions, priority queue, multiple source types |
| `<<` operator direction | Paper Table 1: "id₂ can be reached from id₁" | Our `ReachablePathMatch(descendant=id₁, ancestor=id₂)` — field names are misleading but semantics match: id₁ is the container, id₂ is the target |
| Localised action dispatch | Neverlang attaches "agents" to matched PT nodes | We wrap handlers with node-identity checks; requires reusing the same parse tree (no reparse after localised adaptation) |

## References

- Cazzola, W., Chitchyan, R., Rashid, A., Shaqiri, A. (2017). *μ-DSU: A Micro-Language Based Approach to Dynamic Software Updating*. Computer Languages, Systems & Structures.
- Cazzola, W. (2012). *Neverlang*. Modular language development framework.
- Chitchyan, R. et al. (2014). *Micro-languages for change propagation scoping*.
