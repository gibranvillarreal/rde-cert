# AI Collaboration Log — Smart Backlog Assistant

This document captures how this project was designed and built through an iterative
conversation with Claude (via Claude Code). It is intended to show evaluators the
AI-assisted development process: the decisions made, the alternatives rejected, and
the reasoning behind the final architecture.

---

## Phase 1 — Problem Framing & Approach

### Starting point
The project brief was brought to Claude Code with an open question: *"What's the best
approach to build this, using Claude's full potential — skills, MCP servers, rules,
RAG/GraphRAG, PostgreSQL?"*

Rather than immediately starting to build, the first conversation was a critical design
review. Claude pushed back on several ideas before any code was written.

### Key decisions made in this phase

**GraphRAG — rejected**
GraphRAG was discussed as a potential approach for understanding relationships between
requirements. It was rejected because the actual problem — meeting notes + a backlog JSON
file — fits comfortably in Claude's context window. GraphRAG would add graph construction
pipelines and significant setup complexity without solving a problem that actually exists
at this scope. A well-executed simple solution was preferred over an incomplete complex one.

**RAG with pgvector — deferred, not rejected**
PostgreSQL with pgvector was discussed for duplicate detection. The decision was to build
a prompt-based dedup check first, and design the `retrieval/` module so that pgvector
can be swapped in later without touching the pipeline. This is reflected in
`retrieval/simple.py` — the module exists and has the right interface, but uses Claude
instead of a vector database. Future addition requires only replacing that one file.

**Filesystem MCP server — rejected on security grounds**
Claude initially suggested using the filesystem MCP server to let Claude natively browse
input files. The user correctly flagged a security concern: on a managed corporate
(Accenture) laptop, any file contents read via MCP are sent to Anthropic's API, which
could conflict with DLP (Data Loss Prevention) policies. The filesystem MCP was dropped
entirely. File I/O is handled inside the Python application itself, which is the correct
approach for a corporate environment.

**Web UI — rejected**
A web UI was discussed and deliberately excluded. The evaluation criteria rewards a
working solution over a feature-complete one. A CLI tool that demonstrably works is
a stronger submission than a half-finished web app.

**Final stack chosen**
- Python CLI with `click`
- Anthropic SDK with tool use, prompt caching, and structured output
- `pypdf` for PDF parsing
- No database, no web framework, no external services

---

## Phase 2 — Architecture Design

### Stable pipeline contract
The central architectural decision was to define a stable contract for the pipeline:

```python
def run(notes_text: str, existing_backlog: list[dict], verbose: bool = False) -> dict:
```

This signature does not change when a UI, RAG layer, or GraphRAG is added later. All
future features (a FastAPI wrapper, pgvector retrieval, Streamlit UI) plug around this
function, not inside it. This was an explicit design goal discussed before any code
was written.

### Module boundaries designed for extension
The directory structure was designed with future extension points in mind:

| Directory | Current use | Future extension |
|---|---|---|
| `parsers/` | `.txt` and `.pdf` | Add Jira, Confluence, URL parsers |
| `retrieval/` | Prompt-based dedup | Swap in pgvector RAG |
| `outputs/` | JSON + stdout | Add Markdown, CSV, Jira push |
| `main.py` → `api.py` | CLI | Wrap with FastAPI for UI layer |

The rule: each module exposes a consistent interface. The pipeline never changes; only
the modules that feed into it or consume from it evolve.

### Documentation before code
The user suggested creating architecture and planning documents before writing any
implementation. This produced three foundational files:

- `CLAUDE.md` — project briefing that Claude Code reads automatically at session start
- `docs/architecture.md` — full technical specification, data flow, schemas, extension points
- `docs/devplan.md` — 12 sequenced tickets with acceptance criteria and effort estimates

This approach mirrors good engineering practice: align on the design before building.
It also gave us a concrete checklist to build from, and gives evaluators a clear picture
of what was planned vs. what was delivered.

### Claude Code integration
Several Claude Code-specific features were incorporated:

- **CLAUDE.md** — automatically loaded by Claude Code at every session start, meaning
  Claude understands the project context without re-explanation
- **Custom slash commands** — `/project:run-sample` and `/project:test-all` in
  `.claude/commands/` allow running the tool directly from within Claude Code
- **Scoped permissions** — `.claude/settings.json` limits Claude Code to only `python`
  and `pip` commands in this project directory, a deliberate security boundary

---

## Phase 3 — Iterative Build

The project was built ticket by ticket, following the devplan. Build order:

### Ticket 1 — Project setup
Directory structure, `requirements.txt`, `.env.example`, `.claude/settings.json`, and
a skeleton `main.py` that passes `--help`. Goal: verify the project runs before building
any logic.

### Tickets 2 + 3 — Parsers and prompts (parallel)
Parsers (`text.py`, `pdf.py`) and the prompt/schema files were built simultaneously
since they have no dependency on each other.

**Prompt engineering decisions made here:**

The decision was made to split the work into 4 focused prompts rather than one
large prompt. Each prompt has a single responsibility:

1. `EXTRACTION_PROMPT` — extract only, no interpretation
2. `DEDUP_PROMPT` — compare only, return strict JSON
3. `GENERATION_PROMPT` — generate only, forced via tool use schema
4. `CRITIQUE_PROMPT` — review only, return strict JSON

This is a deliberate prompt engineering choice. A single prompt trying to extract,
deduplicate, generate, and review produces worse results than four focused prompts.
It also makes failures easier to diagnose — if something goes wrong, you know which
step it came from.

The `DEDUP_PROMPT` and `CRITIQUE_PROMPT` instruct Claude to return *only* JSON with
no explanation. This is intentional: free-form text responses require fragile parsing.
Strict output format instructions are the practical way to get reliable structured output
without tool use.

The `GENERATION_PROMPT` uses Claude's tool use feature with a defined `UserStory` schema.
This is the strongest guarantee of structured output — Claude cannot return a story
that is missing required fields or uses invalid enum values.

A few-shot example was added to `GENERATION_PROMPT` showing a well-formed user story.
Few-shot examples significantly improve output consistency for structured tasks.

### Tickets 4–7 — Pipeline steps
The four pipeline steps were implemented in a single `pipeline.py` file:

- Each step is a named function — easy to test and replace independently
- A shared `_call_api()` helper centralizes all API calls, retry logic, and prompt caching
- The system prompt is marked `cache_control: ephemeral` on every call — this reduces
  token cost on repeated calls within a session (effective when processing multiple
  documents)
- Two early-exit paths in `run()`: no requirements extracted, and all requirements
  already in backlog — both return gracefully rather than erroring

**The self-critique loop (Step 4)** deserves specific mention. After generating stories,
a second Claude call reviews them for vagueness, size, and missing acceptance criteria,
then produces corrected versions. This demonstrates iterative AI reasoning — a key
concept the evaluators are looking for. It adds roughly 20 lines of code and one API
call, but significantly improves output quality.

### Tickets 8 + 9 — Output and CLI wiring
The formatter prints a structured terminal summary alongside the JSON output so reviewers
can see results without opening a file. The CLI validates inputs before reaching the
pipeline: file type checking, JSON validation on the backlog, and a clear check for
the API key. Error messages are directed to stderr so they don't pollute the JSON output.

---

## Phase 4 — Security and Hygiene

A `.gitignore` was created at the end covering:
- `.env` (API key protection)
- `user_stories.json` (generated output is not source code)
- `samples/results/` (test outputs)
- Python bytecode and virtual environments

This was a deliberate final step — the project is designed to be safely committed to
a repository without risk of leaking credentials.

---

## Summary of Key Tradeoffs

| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| Output structure | Tool use schema | Free-form text | Reliable, parseable, no post-processing |
| Prompt design | 4 focused prompts | 1 mega-prompt | Easier to debug, better quality |
| Dedup method | Prompt-based | pgvector RAG | Sufficient for scope; RAG is a drop-in swap |
| File I/O | Python `open()` | Filesystem MCP | Corporate laptop DLP concerns |
| Interface | CLI | Web UI | Scope discipline; working > feature-complete |
| AI orchestration | Custom pipeline | LangChain/similar | Fewer dependencies, full visibility |

---

## What Worked Well

- **Documentation before code** — having `devplan.md` as a checklist made the build
  feel systematic rather than exploratory. Every ticket had clear acceptance criteria.
- **Stable pipeline contract** — designing `run()` first meant all modules were built
  to serve a known interface, not the other way around.
- **Tool use for structured output** — zero post-processing needed on story generation.
  The schema enforces correctness at the API level.
- **Prompt separation** — having all prompts in `prompts.py` made iteration fast. When
  a prompt needed adjustment, there was one place to change it.

## What Would Be Improved Next

- **Prompt caching effectiveness** — the system prompt alone may not reach the 1024
  token minimum required for caching on `claude-sonnet-4-6`. A future improvement would
  combine the system prompt with the backlog content into a single cached block that
  reliably meets the threshold.
- **pgvector dedup** — the prompt-based dedup is good but semantic similarity via
  embeddings would catch paraphrased duplicates more reliably.
- **Streaming output** — the pipeline currently waits for each step to complete before
  printing. Adding `stream=True` would give real-time feedback during long generations.
- **Batch processing** — running against multiple meeting notes files in one command
  would be a natural next feature, requiring only a loop over `pipeline.run()`.
