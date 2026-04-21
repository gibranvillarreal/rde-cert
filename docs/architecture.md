# Architecture — Smart Backlog Assistant

## Problem Statement
Engineers spend significant time manually converting meeting notes and requirement
documents into structured backlog items. The process is inconsistent, slow, and
easy to miss requirements. This tool automates that conversion using a multi-step
AI pipeline backed by Claude.

## Use Cases
1. **Sprint planning** — paste in meeting notes, get groomed backlog items ready for review
2. **Client requirements session** — process a requirements doc and extract structured stories
3. **Backlog hygiene** — detect what new requirements are already covered in the existing backlog

---

## Tech Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Fast iteration, strong AI library support |
| AI Model | Claude claude-sonnet-4-6 | Best balance of quality and speed for structured output |
| AI SDK | `anthropic` (official) | Tool use, prompt caching, streaming support |
| PDF parsing | `pypdf2` | Lightweight, no external dependencies |
| CLI | `click` | Clean argument handling, easy to extend |
| Output | JSON + plain text summary | Simple, parseable, no UI required |
| Future DB | PostgreSQL + pgvector | RAG-based dedup (not in current scope) |

---

## Module Responsibilities

### `main.py` — CLI only
Parses arguments, calls the right parser, calls `pipeline.run()`, writes output.
No business logic lives here.

### `pipeline.py` — Stable core
Orchestrates the 4-step prompt chain. This is the contract:
```python
def run(requirements_text: str, existing_backlog: list[dict]) -> dict:
    # Returns: {"stories": [...], "summary": "...", "duplicates": [...]}
```
This signature does not change when UI, RAG, or GraphRAG is added.

### `prompts.py` — All prompt templates
Every prompt string lives here as a named constant or function.
No prompt text is allowed to live inline in pipeline or business logic.
Makes prompt iteration, versioning, and documentation trivial.

### `schemas.py` — Tool use schemas
All JSON schemas for Claude tool use live here.
Single source of truth for output shape.

### `parsers/text.py` and `parsers/pdf.py`
Both expose the same interface:
```python
def parse(file_path: str) -> str:
    # Returns: plain text content
```
New parsers (Jira, Confluence, URL) follow the same interface.

### `retrieval/simple.py`
Prompt-based dedup check. Takes requirements list + backlog, returns:
```python
{"new": [...], "duplicates": [...]}
```
Future replacement: pgvector cosine similarity search with the same return shape.

### `outputs/formatter.py`
Takes the pipeline result dict, writes `user_stories.json` and prints a plain text summary.
Future: add `markdown_formatter.py`, `csv_formatter.py`, `jira_formatter.py`.

---

## Pipeline — Step by Step

```
┌─────────────────────────────────────────────────────────┐
│                      INPUT LAYER                        │
│  meeting_notes.txt/.pdf   +   backlog.json              │
└────────────────┬───────────────────────┬────────────────┘
                 │                       │
                 ▼                       ▼
         parsers/text.py          loaded as list[dict]
         parsers/pdf.py
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│               STEP 1 — REQUIREMENT EXTRACTION           │
│  Prompt: extract clean, atomic requirements from text   │
│  Output: list of requirement strings                    │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│               STEP 2 — DEDUP CHECK                      │
│  Prompt: compare requirements against existing backlog  │
│  Output: {new: [...], duplicates: [...]}                │
└────────────────────────────┬────────────────────────────┘
                             │ (only new requirements)
                             ▼
┌─────────────────────────────────────────────────────────┐
│               STEP 3 — STORY GENERATION (tool use)      │
│  Schema: UserStory with title, as_a, i_want, so_that,   │
│          acceptance_criteria, priority, category        │
│  Output: list[UserStory] as structured JSON             │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│               STEP 4 — SELF-CRITIQUE & REFINE           │
│  Prompt: review stories for vagueness, size, quality    │
│  Output: refined list[UserStory] + summary              │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                        │
│  user_stories.json   +   printed summary                │
└─────────────────────────────────────────────────────────┘
```

---

## Tool Use Schema — UserStory

```json
{
  "name": "create_user_story",
  "description": "Create a single structured user story from a requirement",
  "input_schema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "Short story title (max 10 words)"
      },
      "as_a": {
        "type": "string",
        "description": "The user role (e.g. 'product manager', 'developer')"
      },
      "i_want": {
        "type": "string",
        "description": "The desired action or feature"
      },
      "so_that": {
        "type": "string",
        "description": "The business value or outcome"
      },
      "acceptance_criteria": {
        "type": "array",
        "items": {"type": "string"},
        "description": "2-4 testable conditions for this story to be complete",
        "minItems": 2,
        "maxItems": 4
      },
      "priority": {
        "type": "string",
        "enum": ["high", "medium", "low"]
      },
      "category": {
        "type": "string",
        "enum": ["feature", "bug", "tech-debt", "research"]
      },
      "estimated_complexity": {
        "type": "string",
        "enum": ["small", "medium", "large"],
        "description": "Rough complexity estimate"
      }
    },
    "required": ["title", "as_a", "i_want", "so_that", "acceptance_criteria", "priority", "category", "estimated_complexity"]
  }
}
```

---

## Prompt Engineering Approach

### Principles
- Each step has a single, focused responsibility
- Prompts use explicit output format instructions
- System prompt establishes role and context once (cached)
- Few-shot examples included for story generation step
- Self-critique step uses a checklist format for consistency

### Prompt Caching Strategy
The system prompt and existing backlog JSON are marked for caching.
Repeated calls within a session (e.g. processing multiple documents) pay ~10% token cost.

```python
# Cached block — processed once per session
{"type": "text", "text": SYSTEM_PROMPT + backlog_json, "cache_control": {"type": "ephemeral"}}
```

---

## Error Handling
- File not found → clear CLI error message, exit 1
- PDF parse failure → fallback to raw text extraction, warn user
- API timeout → retry once with exponential backoff, then fail with message
- Malformed tool use response → log raw response, raise descriptive exception
- Empty requirements extracted → warn user, exit gracefully (not an error)

---

## Future Extension Points

| Feature | Where It Plugs In | Effort |
|---|---|---|
| FastAPI/Streamlit UI | New `api.py` wrapping `pipeline.run()` | Low |
| pgvector RAG dedup | Replace `retrieval/simple.py` implementation | Medium |
| GraphRAG | New `retrieval/graphrag.py` for entity-aware retrieval | High |
| Jira integration | New `parsers/jira.py` + `outputs/jira_formatter.py` | Medium |
| Confluence input | New `parsers/confluence.py` | Low |
| Streaming output | Add `stream=True` to pipeline calls | Low |
| Batch processing | Loop over files, call `pipeline.run()` per file | Low |

---

## Out of Scope (Current Version)
- Web UI
- Authentication / multi-user
- Database persistence
- Real-time Jira/Linear sync
- Fine-tuned models
