# Paper Conformance Report

Systematic verification of this implementation against the original paper:

> Cazzola, Chitchyan, Rashid, Shaqiri. *"μ-DSU: A Micro-Language Based Approach to Dynamic Software Updating"*, Computer Languages, Systems & Structures, 2017. DOI: 10.1016/j.cl.2017.07.003

## Methodology

We verify against the **paper's text**, not the original Neverlang/Java source code (which was never published). Three levels of verification:

1. **Input→Output tests** ([`tests/test_paper_io.py`](../tests/test_paper_io.py)) — feed exact inputs from the paper, verify exact outputs. The strongest evidence.
2. **Exact-match tests** ([`tests/test_paper_exact_match.py`](../tests/test_paper_exact_match.py)) — verify specific numerical values, sets, and structures stated verbatim in the paper.
3. **Conformance tests** ([`tests/test_paper_conformance.py`](../tests/test_paper_conformance.py)) — verify behavioral properties and architectural claims.

## Input→Output Verification

These tests run the actual programs from the paper's listings with specific inputs and compare outputs to what the paper describes.

### Fig. 2(a) — Vacuum Cleaner Default Behaviour

The paper shows a state diagram: `on ←click→ off`.

| Input (click sequence) | Expected state trace | Our output | Status |
|---|---|---|---|
| `[True, True, True, True]` | on → off → on → off → on | `["on", "off", "on", "off", "on"]` | exact match |
| `[False, False, False]` | on → on → on → on | `["on", "on", "on", "on"]` | exact match |
| `[False, True, False, True]` | on → on → off → off → on | `["on", "on", "off", "off", "on"]` | exact match |

> Test: `test_paper_io.py::TestIO_Fig2a_VacuumDefault`

### Fig. 2(b) — Vacuum Cleaner with Stand-by

Paper Sect. 3.2: *"if it is not in motion for 10 seconds, it is considered not in use"*. The counter `t` increments each time stand-by is entered. When `t > 10`, the `elapsed` event fires and transitions to `off`.

| Input | Expected output | Our output | Status |
|---|---|---|---|
| inactivity=True, 12 steps | on → stand-by (×11) → off | `trace[0]="on"`, `trace[1..11]="stand-by"`, `trace[12]="off"` | exact match |
| stand-by + activity (inactivity off) | stand-by → on, t resets to 0 | `current_state="on"`, `t=0` | exact match |
| stand-by + click | stand-by → off | `current_state="off"` | exact match |

> Test: `test_paper_io.py::TestIO_Fig2b_VacuumStandby`

### Sect. 5.1 — HTML Viewer Accessibility

Paper Table 2 defines three language features: `print Expr`, `set font size Expr`, `set font color Expr`. Paper p.15: hyperopic *"multiplied by 3 to increase the size"*, blind *"reads it aloud using a specific library"*.

| Input | Profile | Expected output | Our output | Status |
|---|---|---|---|---|
| `set font size 12; print "Hello";` | healthy | {text="Hello", size=12, color="red"} | `{"text": "Hello", "size": 12, "color": "red", "profile": "healthy"}` | exact match |
| same program + adaptation | hyperopic | {text="Hello", size=**36**} | `{"size": 36, "profile": "hyperopic"}` | exact match (12×3=36) |
| same program + adaptation | blind | {text="Hello"} + speech=["Hello"] | output + `__speech__=["Hello"]` | exact match |
| `print "line1"; print "line2";` + blind | blind | both prints change, both spoken | `speech=["line1", "line2"]` | exact match |

> Test: `test_paper_io.py::TestIO_Sect51_HTMLViewer`

### Sect. 3.2 — Seamless Adaptation

Paper: *"any program written in this language will remain unaltered, yet will incorporate the new behaviour"*.

| Scenario | Program text | Output before | Output after | Program changed? | Status |
|---|---|---|---|---|---|
| healthy → hyperopic | `set font size 12; print "test";` | size=12 | size=36 | **No** (identical string) | exact match |

> Test: `test_paper_io.py::TestIO_SeamlessAdaptation`

### Sect. 5.2 + Fig. 5 — Mandelbrot Parallelisation

Paper identifies three scenarios (Fig. 5): (a) both for sequential, (b) both for parallel (system-wide), (c) outer sequential + inner parallel (localised).

Program: nested `for` loop, 3 outer × 4 inner = 12 iterations.

| Adaptation | Expected total | Expected execution modes | Our total | Our modes | Status |
|---|---|---|---|---|---|
| None | 12 | all sequential | 12 | 4× "sequential" | exact match |
| System-wide for→parfor | 12 | all parallel | 12 | 4× "parallel" | exact match |
| Localised inner-only | 12 | 1 sequential + 3 parallel | 12 | 1× "sequential" + 3× "parallel" | exact match |

Key result: **same computation (total=12) regardless of execution strategy** — only the mode differs. This matches the paper's claim that parallelisation does not affect correctness.

> Test: `test_paper_io.py::TestIO_Sect52_Mandelbrot`

## Exact-Match Verification

Values stated verbatim in the paper that we reproduce exactly.

### Listing 2a — Default Program Structure

| Paper claim | Our value | Status |
|---|---|---|
| States = {on, off} | `{"on", "off"}` | exact match |
| Events = {click} | `{"click"}` | exact match |
| Transitions: on {click⇒off} | `[("click", "off")]` | exact match |
| Transitions: off {click⇒on} | `[("click", "on")]` | exact match |

> Test: `test_paper_exact_match.py::TestExact_Listing2a`

### Listing 2b — Extended Program Structure

| Paper claim | Our value | Status |
|---|---|---|
| counter t initialized to 0 | `t == 0` | exact match |
| States = {on, off, stand-by} | `{"on", "off", "stand-by"}` | exact match |
| Events = {click, elapsed, activity, inactivity} | `{"click", "elapsed", "activity", "inactivity"}` | exact match |
| on = turn-on ; t←0 | entering "on" → `t = 0` | exact match |
| stand-by = t←t+1 | `t=7` → entering stand-by → `t = 8` | exact match |
| elapsed = t > 10 | `t=10` → False, `t=11` → True | exact match |
| stand-by transitions (4, in order) | click⇒off, elapsed⇒off, inactivity⇒stand-by, activity⇒on | exact match |

> Test: `test_paper_exact_match.py::TestExact_Listing2b`

### Micro-Language Definitions (p.7, p.15, p.17)

| Paper definition | Verified property | Status |
|---|---|---|
| μ_ton ∩ μ_toff = {state_init, transition_def} | 2 shared features | exact match |
| μ_show = {set font color, set font size, print} | 3 features | exact match |
| μ_calc = {while, =, -, +, *, >, &&} | 7 features | exact match |
| μ_cols = {for, =, -, /, <, ++} | 6 features | exact match |
| μ_rows = {for, =, <, ++} | 4 features | exact match |
| μ_cols ∩ μ_rows | 4 shared features | exact match |

> Test: `test_paper_exact_match.py::TestExact_MicroLanguageDefinitions`

### Listing 5(b) — Hyperopic Font Multiplication

| Paper claim | Our value | Status |
|---|---|---|
| *"multiplied by 3 to increase the size"* (p.15) | input size=12 → output size=36 | exact match |

> Test: `test_paper_exact_match.py::TestExact_Listing5b_Hyperopic`

### Listing 5(c) — Blind Text-to-Speech

| Paper claim | Our value | Status |
|---|---|---|
| *"reads it aloud using a specific library"* (p.15) | `__speech__ = ["hello world"]` | exact match |

> Test: `test_paper_exact_match.py::TestExact_Listing5c_Blind`

### Listing 6(b) — μDA Script Structure

| Paper claim | Our parse result | Status |
|---|---|---|
| 2 slice bindings (old, new) | `context[0].names=["old"], context[1].names=["new"]` | exact match |
| 1 replace + 1 redo | `operations = [ReplaceSlice, RedoRole]` | exact match |
| qualified names match | `sustainability.HealthyPrint`, `sustainability.BlindPrint` | exact match |

> Test: `test_paper_exact_match.py::TestExact_Listing6b`

### Listing 3 — HooverLang Slice Count

| Paper claim | Our value | Note | Status |
|---|---|---|---|
| 13 slices listed | 10 slices | 3 list-wrapper slices (StateLst, EventList, TransList) absorbed by Lark's `+` operator | accounted deviation |

> Test: `test_paper_exact_match.py::TestExact_Listing3`

## Conformance Verification

Architectural and behavioral properties claimed in the paper.

### Table 1 — μDA DSL Operations

All 12 operations from Table 1 parse correctly in our μDA grammar:

| Category | Operation | Parses? | Executes? | Notes |
|---|---|---|---|---|
| Context | `[endemic] slice «id» : «slc» ;` | yes | partial | `endemic` flag parsed and stored but not enforced at runtime (no module namespace scoping); see Known Deviations |
| Context | `nt «id» : «rule» from module «mod» ;` | yes | yes | |
| Context | `production «id» : «rule» from module «mod» ;` | yes | yes | Accepted as grammar-level synonym for `nt`; both resolve identically |
| Context | `action «id» : «nt» from module «mod» role «name» ;` | yes | yes | |
| Matching | `«id»[«cond»]` (node match) | yes | yes | |
| Matching | `«id1» < «id2» [│ «id»]` (parent path) | yes | yes | |
| Matching | `«id1» << «id2» [│ «id»]` (reachable path) | yes | yes | |
| Manipulation | `add action «id» [to «id»] in role «name» ;` | yes | yes | `to «id»` used as target filter on matched nodes |
| Manipulation | `remove action «id» [from «id»] in role «name» ;` | yes | yes | `from «id»` used as target filter on matched nodes |
| Manipulation | `set specialized action for «id» to «id» in role «name» ;` | yes | yes | |
| System-wide | `replace slice «id1» with «id2» ;` | yes | yes | |
| System-wide | `redo [from «node»] [role «name»] ;` | yes | yes | `from «node»` executes from the first matching subtree |

> Test: `test_paper_conformance.py::TestTable1_MuDaDSL`

### Fig. 3 — Architecture Components

| Component | Paper | Our implementation | Present? |
|---|---|---|---|
| ① Framework for modular language development | Neverlang | `GrammarComposer` + `LanguageSlice` | yes |
| ② Language interpreter | Neverlang interpreter | `Interpreter` (tree-walking, pluggable actions) | yes |
| ③ Event manager | Bash scripts | `EventManager` + `EventBus` + sources | yes |
| ④ Micro-language adapter | μDA executor | `MicroLanguageAdapter` + `MuDaParser` | yes |
| ⑤ Analysis | *"currently under investigation"* | `FeatureAnalyzer` (AST + LLM) | yes (novel) |

> Test: `test_paper_conformance.py::TestFig3_Architecture`

### Sect. 4.2 — Two Adaptation Modes

| Mode | Paper description | Our implementation | Verified? |
|---|---|---|---|
| System-wide | *"replacing a language component affecting every use"* | `replace slice` + `redo` — all prints change to blind | yes |
| Localised | *"modify a language feature locally to a single use"* | `when ... << ... occurs` — only inner for becomes parallel | yes |

> Test: `test_paper_conformance.py::TestSect42_AdaptationModes`

## Known Deviations

| Area | Original (Neverlang/Java) | Our implementation | Reason |
|---|---|---|---|
| Slice count | 13 slices for HooverLang | 10 slices | Lark's `+` absorbs StateLst/EventList/TransList |
| Grammar composition | Neverlang merges at framework level | Lark string concatenation + rule merging | Different parsing framework |
| Parser hot-swap | In-place without regeneration | Full parser rebuild (cached) | Lark limitation |
| `production` binding | Separate from `nt` | `production` accepted as grammar synonym for `nt`; both resolve identically | Functionally equivalent |
| Event manager | Bash `while true; do` loop | Async `EventManager` with typed events | Intentional improvement |
| `<<` operator | Not fully specified in paper | Interpreted as "from id₁ reach id₂" | Our best reading of Table 1 |
| Localised dispatch | Neverlang "agents" on PT nodes | Handler wrapping with node-identity check | Requires same parse tree (no reparse after localised adaptation) |
| Component ⑤ | *"Under investigation"* | Implemented with AST analysis + LLM | Novel contribution |
| `endemic` keyword | Scope-limits a slice to the defining module | Flag parsed and stored (`SliceBinding.endemic`) but not enforced at runtime | No Neverlang module namespace system; would require namespace scoping layer |
| Localised `target_name` | `add action X to Y` / `remove action X from Y` target a specific nonterminal | `target_name` used as filter: only matched nodes whose type matches `target_name` receive the action. Targeting is achieved via path expression + node identity filtering, not via the Neverlang agent mechanism | Behavioral equivalence; mechanistic difference |
| Event subscriptions | Paper links event → feature → micro-language context | `Subscription.micro_language` and `Subscription.context` fields defined but unused; event→adaptation link works through `adaptation_script` directly | Simpler model; the script itself carries full context |
| Localised adaptation model | Neverlang attaches "agents" to AST/PT nodes that intercept dispatch | We wrap action handlers with node-identity closures (`_make_node_filtered_action`); this requires reusing the same parse tree instance — reparsing creates new node objects and breaks identity | Documented engineering tradeoff; behavioral equivalence confirmed by study 3 (Mandelbrot localised parallelisation) |

## Summary

| Test suite | Tests | Pass rate | What it proves |
|---|---|---|---|
| [`test_paper_io.py`](../tests/test_paper_io.py) | 15 | 100% | Same inputs produce same outputs as described in paper |
| [`test_paper_exact_match.py`](../tests/test_paper_exact_match.py) | 19 | 100% | Specific values from paper text are reproduced exactly |
| [`test_paper_conformance.py`](../tests/test_paper_conformance.py) | 54 | 100% | Architectural and behavioral properties hold |
| **Total** | **88** | **100%** | |

**Caveat:** All verification is against the paper's text. The original Neverlang/Java source code was never published. We cannot guarantee bit-for-bit equivalence with the original implementation — only that our system behaves as the paper describes.

## Conformance Level

This is a **paper-faithful reimplementation** — behavioral equivalence at the level of architecture, studies, and DSL semantics. It is **not** a mechanistic port of the Neverlang runtime. Specific distinctions:

- **Behavioral equivalence** (confirmed): all three studies produce the same outputs as the paper describes; all 12 Table 1 operations are parsed; system-wide and localised adaptation modes work as specified.
- **Mechanistic differences** (documented above): localised dispatch uses handler wrapping instead of PT agents; `endemic` scoping is not enforced; event→micro-language link is simplified.
- **Grammar coverage**: all Table 1 forms including `production` (as `nt` synonym) are accepted. The `redo` operation supports both `from «node»` and `role «name»` optional arguments.
