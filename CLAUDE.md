# Smart Backlog Assistant — Claude Context

## What This Project Does
A Python CLI tool that processes meeting notes (text/PDF) and an existing backlog (JSON),
then runs a multi-step AI pipeline to generate structured user stories with acceptance
criteria, priority, and category. Designed to help engineers turn raw meeting output into
ready-to-groom backlog items.

## Stack
- Python 3.11+
- Anthropic SDK (`anthropic`) — Claude claude-sonnet-4-6
- pypdf2 — PDF parsing
- click — CLI interface
- No database for now (future: pgvector for RAG-based dedup)

## Project Structure
```
backlog_assistant/
├── main.py              # CLI entry point only
├── pipeline.py          # orchestrates the 4-step prompt chain
├── prompts.py           # all prompt templates
├── schemas.py           # tool use JSON schemas
├── parsers/
│   ├── text.py          # .txt file parsing
│   └── pdf.py           # PDF parsing
├── retrieval/
│   └── simple.py        # prompt-based dedup check (future: pgvector)
├── outputs/
│   └── formatter.py     # JSON + summary writer
└── samples/             # test inputs for demo
```

## How to Run
```bash
pip install -r requirements.txt
python main.py --notes samples/meeting1.txt --backlog samples/backlog.json
python main.py --notes samples/meeting1.pdf --backlog samples/backlog.json --output stories.json
```

## Pipeline Overview
```
Input (notes + backlog)
  → Step 1: Extract requirements from notes
  → Step 2: Dedup check against existing backlog
  → Step 3: Generate structured user stories (tool use)
  → Step 4: Self-critique and refine
  → Output: user_stories.json + summary
```

## Key Design Decisions
- Pipeline contract (`pipeline.run(text, backlog) → dict`) is stable — UI/RAG/GraphRAG plug around it
- All prompts live in `prompts.py` — never inline prompts in business logic
- All schemas live in `schemas.py` — single source of truth for output shape
- Prompt caching applied to system prompt + backlog context
- See `docs/architecture.md` for full tech spec
- See `docs/devplan.md` for ticket status and build order

## Claude Code Slash Commands
- `/project:run-sample` — run pipeline against samples/meeting1.txt
- `/project:test-all` — run all three sample scenarios

## Extension Points (Future)
- `parsers/` → add Jira, Confluence, URL parsers
- `retrieval/` → swap simple.py for pgvector RAG
- `outputs/` → add Markdown, CSV, Jira push formatters
- Add `api.py` wrapping `pipeline.py` for a FastAPI/Streamlit UI layer
