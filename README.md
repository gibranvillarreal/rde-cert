# Smart Backlog Assistant

An AI-powered CLI tool that turns meeting notes into structured, ready-to-groom
backlog items using a multi-step Claude pipeline.

## What It Does

Takes two inputs — a meeting notes file and an existing backlog — and produces
structured user stories with acceptance criteria, priority, category, and complexity.
It also detects requirements already covered by the backlog to avoid duplicates.

```
meeting_notes.txt  ─┐
                    ├─→ Extract → Dedup → Generate → Critique → user_stories.json
backlog.json       ─┘
```

## Setup

**1. Clone and install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set your API key**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
# Basic run
python main.py --notes samples/meeting1.txt --backlog samples/backlog.json

# With verbose pipeline output
python main.py --notes samples/meeting1.txt --backlog samples/backlog.json --verbose

# Custom output path
python main.py --notes notes.txt --backlog backlog.json --output results/stories.json

# PDF input
python main.py --notes samples/meeting3.pdf --backlog samples/backlog.json
```

Supported input formats: `.txt`, `.md`, `.pdf`

### Converting a text file to PDF

The repo includes a utility to convert any `.txt` file to PDF — useful for testing the PDF
parsing path without needing an external tool:

```bash
pip install fpdf2
python samples/generate_pdf.py samples/meeting3.txt          # → samples/meeting3.pdf
python samples/generate_pdf.py notes.txt --output out.pdf    # custom output path
```

## Pipeline

The tool runs a 4-step prompt chain:

| Step | What it does |
|---|---|
| 1. Extract | Pulls atomic requirements from raw notes |
| 2. Dedup | Identifies which requirements already exist in the backlog |
| 3. Generate | Creates structured user stories via Claude tool use |
| 4. Critique | Reviews stories for quality and refines any that are vague or oversized |

Each step is a focused, single-responsibility prompt. See `docs/prompts.md` for
full prompt documentation and design rationale.

## Output

**Terminal:** A readable summary with all generated stories, acceptance criteria,
and any skipped duplicates.

**`user_stories.json`:** Full structured output including metadata, stats, and all stories.

```json
{
  "generated_at": "2026-04-21T10:30:00",
  "source_file": "samples/meeting1.txt",
  "summary": "...",
  "stats": {
    "requirements_found": 5,
    "new_requirements": 4,
    "duplicates_found": 1,
    "stories_generated": 4,
    "issues_refined": 1
  },
  "stories": [...],
  "duplicates_skipped": [...]
}
```

## Project Structure

```
backlog_assistant/
├── pipeline.py       # 4-step prompt chain orchestrator
├── prompts.py        # all prompt templates
├── schemas.py        # tool use JSON schema for user stories
├── parsers/
│   ├── text.py       # .txt / .md parser
│   └── pdf.py        # PDF parser (pypdf)
├── retrieval/
│   └── simple.py     # prompt-based dedup (future: pgvector)
└── outputs/
    └── formatter.py  # JSON writer + terminal summary
```

## Adding Future Features

The pipeline's `run()` signature is stable:
```python
pipeline.run(notes_text: str, existing_backlog: list[dict]) -> dict
```

| Feature | Where it plugs in |
|---|---|
| Web UI (FastAPI/Streamlit) | New `api.py` wrapping `pipeline.run()` |
| RAG-based dedup (pgvector) | Replace `retrieval/simple.py` |
| New input sources (Jira, URL) | New file in `parsers/` |
| New output formats (CSV, Jira push) | New file in `outputs/` |

## Documentation

- `docs/architecture.md` — full technical spec and design decisions
- `docs/prompts.md` — prompt engineering documentation
- `docs/devplan.md` — project tickets and build log
- `docs/ai-collaboration.md` — how this project was designed and built with Claude Code

## Sample Inputs

Three realistic scenarios in `samples/`:

| File | Scenario | Expected duplicates |
|---|---|---|
| `meeting1.txt` | Sprint planning | Export to PDF |
| `meeting2.txt` | Client requirements session | Search, User profile |
| `meeting3.txt` | Security & integration spec | None |

See `samples/expected-outputs.md` for detailed expected output criteria per scenario.

## Claude Code Shortcuts

If you're using [Claude Code](https://claude.ai/code) inside this repo, two slash commands are registered under `.claude/commands/`:

| Command | What it does |
|---|---|
| `/project:run-sample` | Runs the pipeline against `samples/meeting1.txt` with `--verbose` and reviews output quality |
| `/project:test-all` | Runs all three sample scenarios and reports story counts, duplicates, and any issues |

Invoke them from the Claude Code chat panel — no need to type the full `python main.py ...` command manually.

## Requirements

- Python 3.11+
- Anthropic API key (`claude-sonnet-4-6`)
- Dependencies: `anthropic`, `pypdf`, `click`, `python-dotenv`
