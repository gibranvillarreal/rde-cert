# Prompt Engineering Documentation

All prompts live in `backlog_assistant/prompts.py`. This document explains each
prompt's purpose, design decisions, and the reasoning behind key choices.

---

## SYSTEM_PROMPT

**Purpose:** Establishes Claude's role and quality bar for the entire session.
Sent on every API call, cached via `cache_control: ephemeral`.

**Key decisions:**

- Defines the role as "senior business analyst and product manager" — not just "assistant."
  Giving Claude a specific expert role improves output quality for domain-specific tasks.
- Lists concrete quality criteria (specific, testable, user-perspective, sprint-sized)
  rather than vague instructions like "write good user stories."
- Ends with "You are concise and direct" to suppress padding and unnecessary commentary
  in responses, which would complicate JSON parsing downstream.

---

## EXTRACTION_PROMPT

**Purpose:** Step 1 — extract atomic requirements from raw meeting notes.

**Key decisions:**

- Instructs Claude to output *only* a numbered list, nothing else. This makes parsing
  trivial: split on newlines, strip the leading number.
- Explicitly says "Do not invent requirements" — without this instruction, Claude tends
  to infer and add requirements that were implied but not stated.
- "Do not merge requirements together" — prevents Claude from combining related items
  into a single vague requirement, which would produce a story that is too large.
- "Ignore non-requirements" — meeting notes contain scheduling, pleasantries, and
  action items. Without this, Claude includes them as requirements.

**Format instruction:** Numbered list, one requirement per line, nothing else.
This is strict by design — any extra text breaks the line-by-line parser.

---

## DEDUP_PROMPT

**Purpose:** Step 2 — identify which extracted requirements already exist in the backlog.

**Key decisions:**

- Defines "duplicate" explicitly: same functionality even if worded differently.
  Without a clear definition, Claude applies inconsistent matching thresholds.
- Instructs Claude to return **only JSON**, no explanation. Free-form text mixed with
  JSON is unparseable. `json.loads()` is the only processing needed.
- The JSON schema is defined inline in the prompt so Claude knows exactly what structure
  to produce. This is more reliable than describing it in words.
- Uses double curly braces `{{...}}` for literal JSON syntax in the f-string template.

**Format instruction:** Strict JSON with `new` and `duplicates` arrays. No explanation.

**Why not tool use here?**
Tool use would work, but the dedup output is a simple two-key JSON object — not complex
enough to justify the schema overhead. Strict JSON instruction is sufficient and keeps
the prompt lighter.

---

## GENERATION_PROMPT

**Purpose:** Step 3 — convert each new requirement into a structured user story.

**Key decisions:**

- Uses Claude's **tool use** feature with `USER_STORY_SCHEMA`. This is the strongest
  guarantee of structured output: Claude cannot return a story missing required fields
  or using invalid enum values. The schema enforces correctness at the API level.
- `tool_choice: {"type": "any"}` forces Claude to call the tool for every requirement.
  Without this, Claude might choose to respond in text for simple requirements.
- Includes a concrete **few-shot example** of a well-formed story. Few-shot examples
  consistently improve output quality for structured generation tasks. The example
  is marked "for reference only, do not copy" to prevent Claude from reusing it verbatim.
- Priority and complexity guidelines are explicit: "high = blocks other work or critical
  user path" rather than leaving these to Claude's interpretation.

**Format instruction:** Tool use only. Each requirement gets one `create_user_story` call.

---

## CRITIQUE_PROMPT

**Purpose:** Step 4 — review generated stories for quality issues and produce corrections.

**Key decisions:**

- Uses a numbered checklist (vague? too large? testable criteria? specific role?) so
  Claude applies the same checks consistently to every story rather than making
  ad-hoc quality judgments.
- Instructs Claude to "not mention" stories with no issues — this keeps the response
  concise and makes it easy to detect the no-issues case (`refined_stories` is empty).
- Returns strict JSON with `has_issues` boolean — this allows the pipeline to short-circuit
  the merge step when no refinements are needed, avoiding unnecessary processing.
- The `corrected_story` nested object matches the `USER_STORY_SCHEMA` fields exactly,
  so refined stories can be merged back into the original list without transformation.

**Format instruction:** Strict JSON. `has_issues`, `refined_stories`, `summary`. No explanation.

---

## Prompt Iteration Notes

**What changed from v1 to final:**

- `EXTRACTION_PROMPT` v1 asked Claude to "summarize requirements." This produced
  paragraphs instead of atomic items. Changed to "numbered list, one requirement per
  line, nothing else."

- `DEDUP_PROMPT` v1 asked Claude to "identify duplicates and new items." This produced
  a mix of JSON and explanatory text. Changed to explicit JSON schema with "Return
  only the JSON. No explanation."

- `GENERATION_PROMPT` v1 did not include a few-shot example. Early stories had vague
  acceptance criteria ("feature should work as expected"). The example anchors output
  quality.

- `CRITIQUE_PROMPT` v1 asked for a general review. This produced inconsistent checks.
  Changed to a specific numbered checklist so every story is evaluated against the
  same criteria.
