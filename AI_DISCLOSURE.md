# AI Disclosure

## How This Project Was Built

mu-dsu was built with the assistance of AI coding agents:

- **Claude Code** (Anthropic) — primary development agent, architecture design, implementation, testing

The project is a reimplementation of a 2017 academic paper (Cazzola et al., "mu-DSU: A Micro-Language Based Approach to Dynamic Software Updating"). Every design decision, implementation choice, and test case was reviewed by a human developer. The conformance test suite (88 paper verification tests) ensures the implementation accurately reproduces the behavior described in the original paper.

## Runtime LLM Usage

mu-dsu includes an optional LLM-assisted feature analysis module. **All LLM features are opt-in** — the framework works fully offline.

| Feature | What it does | LLM required? |
|---------|-------------|----------------|
| Core framework | Slice composition, grammar merging, interpreter | **No** |
| mu-DA DSL | Parse and execute adaptation scripts | **No** |
| Event manager | Detect events, trigger adaptations | **No** |
| Language execution | Run programs in HooverLang/MiniJS/CalcLang | **No** |
| `mu-dsu analyze` (AST mode) | Identify features from parse tree | **No** |
| `mu-dsu analyze --llm` | LLM-assisted feature identification | Yes (opt-in) |
| `mu-dsu suggest` | Suggest adaptations from natural language | Yes (opt-in) |

### LLM Provider Configuration

When you opt into LLM features, configure the provider via `.env`:

```bash
OPENROUTER_API_KEY=sk-or-...
```

The default model is `google/gemini-3-flash-preview` via OpenRouter. No API keys are configured by default. No data is sent anywhere until you explicitly set up a provider.

## Data Privacy

- mu-dsu does not phone home
- No telemetry, no analytics, no usage tracking
- LLM calls (when enabled) send only the program source and parse tree structure you explicitly analyze — never your environment variables, file system contents, or credentials
