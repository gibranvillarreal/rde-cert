import json
import re
import time

import anthropic
import click

from .prompts import SYSTEM_PROMPT, EXTRACTION_PROMPT, GENERATION_PROMPT, CRITIQUE_PROMPT
from .schemas import USER_STORY_SCHEMA
from .retrieval.simple import check_duplicates

MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 2


def _call_api(client: anthropic.Anthropic, messages: list, tools=None, tool_choice=None, max_tokens=4096):
    """Single API call with one retry on timeout. System prompt is always cached."""
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = {
                "model": MODEL,
                "max_tokens": max_tokens,
                # Cache the system prompt — pays off when processing multiple docs in a session
                "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
            return client.messages.create(**kwargs)
        except anthropic.APITimeoutError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2**attempt)
                continue
            raise


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _log(verbose: bool, msg: str):
    if verbose:
        click.echo(msg)


# ── Step 1 ─────────────────────────────────────────────────────────────────────

def extract_requirements(notes_text: str, client: anthropic.Anthropic, verbose: bool = False) -> list[str]:
    _log(verbose, "  [Step 1] Extracting requirements from notes...")

    response = _call_api(
        client,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(notes=notes_text)}],
    )

    lines = response.content[0].text.strip().split("\n")
    requirements = []
    for line in lines:
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip()).strip()
        if cleaned:
            requirements.append(cleaned)

    _log(verbose, f"     → {len(requirements)} requirements extracted")
    return requirements


# ── Step 3 ─────────────────────────────────────────────────────────────────────

def generate_stories(requirements: list[str], client: anthropic.Anthropic, verbose: bool = False) -> list[dict]:
    _log(verbose, "  [Step 3] Generating structured user stories (tool use)...")

    requirements_text = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(requirements))

    response = _call_api(
        client,
        messages=[{"role": "user", "content": GENERATION_PROMPT.format(requirements=requirements_text)}],
        tools=[USER_STORY_SCHEMA],
        tool_choice={"type": "any"},
        max_tokens=8192,
    )

    stories = [block.input for block in response.content if block.type == "tool_use"]

    if not stories:
        raise ValueError("Story generation returned no tool_use blocks. Check GENERATION_PROMPT and schema.")

    _log(verbose, f"     → {len(stories)} stories generated")
    return stories


# ── Step 4 ─────────────────────────────────────────────────────────────────────

def critique_stories(stories: list[dict], client: anthropic.Anthropic, verbose: bool = False) -> dict:
    _log(verbose, "  [Step 4] Running self-critique and refinement pass...")

    response = _call_api(
        client,
        messages=[{"role": "user", "content": CRITIQUE_PROMPT.format(stories=json.dumps(stories, indent=2))}],
        max_tokens=8192,
    )

    raw = _strip_code_fence(response.content[0].text.strip())
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Critique step returned invalid JSON.\nError: {e}\nRaw: {raw}")

    # Merge refined stories back — replace originals where critique found issues
    if result.get("has_issues") and result.get("refined_stories"):
        refined_map = {r["original_title"]: r["corrected_story"] for r in result["refined_stories"]}
        result["final_stories"] = [
            refined_map.get(story["title"], story) for story in stories
        ]
    else:
        result["final_stories"] = stories

    issues_count = len(result.get("refined_stories") or [])
    _log(verbose, f"     → {issues_count} stories refined")
    return result


# ── Orchestrator ───────────────────────────────────────────────────────────────

def run(notes_text: str, existing_backlog: list[dict], verbose: bool = False) -> dict:
    """
    Main pipeline entry point. Stable contract — signature does not change
    when UI, RAG, or GraphRAG is added around it.

    Returns:
        {
            "stories": list[dict],       # final refined user stories
            "duplicates": list[dict],    # requirements already in backlog
            "summary": str,              # 2-3 sentence summary
            "stats": dict                # counts for each pipeline stage
        }
    """
    client = anthropic.Anthropic()

    # Step 1
    requirements = extract_requirements(notes_text, client, verbose)

    if not requirements:
        return _empty_result("No requirements could be extracted from the provided notes.")

    # Step 2 — delegated to retrieval.simple (swap this module for pgvector RAG later)
    dedup = check_duplicates(requirements, existing_backlog, client, verbose)
    new_requirements = dedup.get("new", requirements)
    duplicates = dedup.get("duplicates", [])

    if not new_requirements:
        return {
            "stories": [],
            "duplicates": duplicates,
            "summary": "All extracted requirements are already covered by the existing backlog.",
            "stats": _stats(len(requirements), 0, len(duplicates), 0, 0),
        }

    # Step 3
    stories = generate_stories(new_requirements, client, verbose)

    # Step 4
    critique = critique_stories(stories, client, verbose)

    return {
        "stories": critique["final_stories"],
        "duplicates": duplicates,
        "summary": critique.get("summary", ""),
        "stats": _stats(
            requirements_found=len(requirements),
            new_requirements=len(new_requirements),
            duplicates_found=len(duplicates),
            stories_generated=len(stories),
            issues_refined=len(critique.get("refined_stories") or []),
        ),
    }


def _empty_result(summary: str) -> dict:
    return {"stories": [], "duplicates": [], "summary": summary, "stats": _stats(0, 0, 0, 0, 0)}


def _stats(requirements_found, new_requirements, duplicates_found, stories_generated, issues_refined) -> dict:
    return {
        "requirements_found": requirements_found,
        "new_requirements": new_requirements,
        "duplicates_found": duplicates_found,
        "stories_generated": stories_generated,
        "issues_refined": issues_refined,
    }
