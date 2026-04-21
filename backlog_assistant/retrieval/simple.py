import json

import anthropic
import click

from ..prompts import DEDUP_PROMPT, SYSTEM_PROMPT


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()


def check_duplicates(
    requirements: list[str], backlog: list[dict], client: anthropic.Anthropic, verbose: bool = False
) -> dict:
    """
    Prompt-based duplicate detection against an existing backlog.

    Returns {"new": [...], "duplicates": [...]}

    Future: replace this implementation with pgvector cosine similarity search
    while keeping the same return shape and function signature.
    """
    if verbose:
        click.echo("  [Step 2] Checking for duplicates against existing backlog...")

    requirements_text = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(requirements))
    backlog_text = json.dumps(backlog, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": DEDUP_PROMPT.format(backlog=backlog_text, requirements=requirements_text),
        }],
    )

    raw = _strip_code_fence(response.content[0].text.strip())
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Dedup step returned invalid JSON.\nError: {e}\nRaw: {raw}")

    if verbose:
        click.echo(f"     → {len(result.get('new', []))} new, {len(result.get('duplicates', []))} duplicates")

    return result
