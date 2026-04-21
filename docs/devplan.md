# Dev Plan — Smart Backlog Assistant

## Status Legend
- `[ ]` Todo
- `[~]` In Progress
- `[x]` Done

---

## Ticket 1 — Project Setup & Scaffolding
**Status:** `[x]`

Set up the base project structure, dependencies, and Claude Code configuration.

**Tasks:**
- Create directory structure (`parsers/`, `retrieval/`, `outputs/`, `samples/`, `docs/`)
- Create `requirements.txt` with initial dependencies
- Create `.claude/settings.json` with scoped permissions
- Create `.claude/commands/run-sample.md` slash command
- Create `.env.example` with required env vars
- Verify `python main.py --help` runs without error

**Acceptance Criteria:**
- Project structure matches `CLAUDE.md`
- `pip install -r requirements.txt` completes without error
- `.claude/settings.json` restricts Claude to only `python` and `pip` commands

---

## Ticket 2 — Input Parsers
**Status:** `[x]`

Implement text and PDF parsers with a consistent interface.

**Tasks:**
- Implement `parsers/text.py` — reads `.txt` file, returns plain string
- Implement `parsers/pdf.py` — reads PDF with `pypdf2`, returns plain string
- Handle encoding errors gracefully in text parser
- Handle corrupted/password-protected PDF gracefully
- Wire parser selection into `main.py` based on file extension

**Acceptance Criteria:**
- `parse("file.txt")` returns string content
- `parse("file.pdf")` returns extracted text
- Unknown file type raises a clear error message
- Both parsers tested manually with sample files

---

## Ticket 3 — Schemas & Prompt Templates
**Status:** `[x]`

Define all tool use schemas and prompt templates before writing pipeline logic.

**Tasks:**
- Create `schemas.py` with `USER_STORY_SCHEMA` tool definition
- Create `prompts.py` with:
  - `SYSTEM_PROMPT` — establishes Claude's role as a senior BA/PM
  - `EXTRACTION_PROMPT` — extracts requirements from raw text
  - `DEDUP_PROMPT` — compares requirements against backlog
  - `GENERATION_PROMPT` — instructs story generation via tool use
  - `CRITIQUE_PROMPT` — reviews generated stories for quality
- Add 2 few-shot examples to `GENERATION_PROMPT`

**Acceptance Criteria:**
- All prompts are strings/functions in `prompts.py` — none defined inline elsewhere
- `USER_STORY_SCHEMA` includes all required fields from architecture doc
- Prompts reviewed manually for clarity and specificity

---

## Ticket 4 — Pipeline Step 1: Requirement Extraction
**Status:** `[x]`

Implement the first step of the pipeline: extract clean requirements from raw text.

**Tasks:**
- Implement `pipeline.py` with `extract_requirements(text: str) -> list[str]`
- Use `EXTRACTION_PROMPT` from `prompts.py`
- Apply prompt caching to system prompt
- Return a clean list of atomic requirement strings
- Log extracted requirements count

**Acceptance Criteria:**
- Given meeting notes text, returns a non-empty list of strings
- Each string is a single, atomic requirement (not a paragraph)
- Works with both short (100 word) and long (2000 word) inputs
- Handles empty/whitespace input gracefully

---

## Ticket 5 — Pipeline Step 2: Dedup Check
**Status:** `[x]`

Compare extracted requirements against the existing backlog to avoid duplicate stories.

**Tasks:**
- Implement `retrieval/simple.py` with `check_duplicates(requirements, backlog) -> dict`
- Use `DEDUP_PROMPT` — pass both lists to Claude for comparison
- Return `{"new": [...], "duplicates": [{"requirement": ..., "matched_item": ...}]}`
- Log how many requirements were flagged as duplicates

**Acceptance Criteria:**
- Returns `new` and `duplicates` keys in all cases
- A requirement clearly matching an existing backlog item is flagged
- A genuinely new requirement is not flagged
- Empty backlog returns all requirements as new

---

## Ticket 6 — Pipeline Step 3: Story Generation (Tool Use)
**Status:** `[x]`

Generate structured user stories from new requirements using Claude tool use.

**Tasks:**
- Implement `generate_stories(requirements: list[str]) -> list[dict]`
- Use `create_user_story` tool schema from `schemas.py`
- Call Claude with `tools=[USER_STORY_SCHEMA]` and `tool_choice={"type": "any"}`
- Parse tool use response into list of story dicts
- Log each generated story title

**Acceptance Criteria:**
- Returns a list of dicts matching the `UserStory` schema
- Each story has all required fields populated
- Priority and category are valid enum values
- Acceptance criteria has at least 2 items per story

---

## Ticket 7 — Pipeline Step 4: Self-Critique & Refinement
**Status:** `[x]`

Add a critique pass that reviews generated stories and flags quality issues.

**Tasks:**
- Implement `critique_stories(stories: list[dict]) -> dict`
- Use `CRITIQUE_PROMPT` — checks for vagueness, size, missing criteria
- Return `{"refined_stories": [...], "issues_found": [...], "summary": "..."}`
- If no issues found, return stories unchanged with empty issues list

**Acceptance Criteria:**
- A vague story (e.g. "improve performance") gets flagged and refined
- A well-written story passes through unchanged
- Summary is a 2-3 sentence paragraph suitable for the output report
- Issues list is empty (not null) when no problems found

---

## Ticket 8 — Output Formatter
**Status:** `[x]`

Write final output to JSON file and print a readable summary to stdout.

**Tasks:**
- Implement `outputs/formatter.py` with `write_output(result: dict, output_path: str)`
- Write `user_stories.json` with full structured output
- Print summary to stdout: story count, duplicates found, categories breakdown
- Include timestamp and input file name in JSON output

**Acceptance Criteria:**
- `user_stories.json` is valid JSON and matches schema
- Stdout summary is readable without opening the JSON file
- Output path defaults to `./user_stories.json` if not specified

---

## Ticket 9 — CLI Entry Point & Wiring
**Status:** `[x]`

Wire everything together in `main.py` and finalize the CLI interface.

**Tasks:**
- Implement `main.py` using `click`
- Arguments: `--notes` (required), `--backlog` (required), `--output` (optional)
- Call correct parser based on file extension
- Call `pipeline.run()` with parsed inputs
- Call `formatter.write_output()` with result
- Add `--verbose` flag that enables step-by-step logging

**Acceptance Criteria:**
- `python main.py --help` shows clear usage
- `python main.py --notes samples/meeting1.txt --backlog samples/backlog.json` runs end to end
- Missing required arguments show helpful error, not a Python traceback
- `--verbose` shows which pipeline step is running

---

## Ticket 10 — Sample Data & Manual Testing
**Status:** `[~]` ← pending your API key test run

Create realistic sample inputs and verify the pipeline produces good output for each.

**Tasks:**
- Create `samples/meeting1.txt` — sprint planning notes (medium complexity, ~300 words)
- Create `samples/meeting2.txt` — client requirements session (longer, ~500 words)
- Create `samples/meeting3.pdf` — a short PDF requirements doc
- Create `samples/backlog.json` — 8-10 existing backlog items (some overlapping with samples)
- Run all three samples manually and document results in `samples/results/`
- Define "good output" criteria for each sample

**Acceptance Criteria:**
- All three samples run without errors
- Sample 1: at least 3 stories generated, all with acceptance criteria
- Sample 2: at least 1 duplicate detected from existing backlog
- Sample 3: PDF parsed and processed correctly
- Output quality reviewed and judged reasonable by developer

---

## Ticket 11 — Claude Code Integration
**Status:** `[x]`

Finalize Claude Code configuration and slash commands for demo use.

**Tasks:**
- Finalize `.claude/settings.json` with correct permissions
- Create `.claude/commands/run-sample.md` — runs meeting1.txt sample
- Create `.claude/commands/test-all.md` — runs all three samples in sequence
- Review and finalize `CLAUDE.md` for accuracy

**Acceptance Criteria:**
- `/project:run-sample` works inside Claude Code session
- `/project:test-all` runs all samples and reports pass/fail
- `CLAUDE.md` accurately reflects final project state

---

## Ticket 12 — Documentation & Reflection
**Status:** `[x]`

Write the final README, document prompts used, and write the reflection section.

**Tasks:**
- Create `README.md` with setup instructions, usage examples, and architecture summary
- Add `docs/prompts.md` documenting each prompt, the reasoning behind it, and iterations
- Add reflection section to `README.md`: what worked, what to improve, AI usage log
- Final review of all code for comments on non-obvious decisions
- Verify the project can be run cleanly by a reviewer with no context

**Acceptance Criteria:**
- A reviewer can clone the repo, run `pip install -r requirements.txt`, and execute the tool in under 5 minutes
- All 4 prompts documented with rationale
- Reflection covers at least 2 things that worked and 2 things to improve
- AI usage log mentions Claude Code usage during development

---

## Build Order

```
Ticket 1  →  Ticket 2  →  Ticket 3
                               ↓
                 Ticket 4 → Ticket 5 → Ticket 6 → Ticket 7
                                                       ↓
                               Ticket 8 → Ticket 9 → Ticket 10
                                                          ↓
                                       Ticket 11 → Ticket 12
```

Tickets 2 and 3 can be done in parallel after Ticket 1.
Tickets 11 and 12 can be partially done throughout (keep CLAUDE.md updated as you go).

---

## Estimated Effort

| Ticket | Effort |
|---|---|
| 1 — Setup | 30 min |
| 2 — Parsers | 45 min |
| 3 — Schemas & Prompts | 60 min |
| 4 — Extraction | 45 min |
| 5 — Dedup | 45 min |
| 6 — Story Generation | 60 min |
| 7 — Self-Critique | 45 min |
| 8 — Output Formatter | 30 min |
| 9 — CLI Wiring | 30 min |
| 10 — Sample Data & Testing | 60 min |
| 11 — Claude Code Integration | 30 min |
| 12 — Documentation | 60 min |
| **Total** | **~9 hours** |
