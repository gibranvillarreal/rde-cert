import json
import os
import sys
from pathlib import Path

import anthropic
import click
from dotenv import load_dotenv

from backlog_assistant import pipeline
from backlog_assistant.outputs import formatter
from backlog_assistant.parsers import pdf, text

load_dotenv()


def _select_parser(file_path: str):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return pdf
    if ext in (".txt", ".md"):
        return text
    raise click.BadParameter(f"Unsupported file type '{ext}'. Use .txt, .md, or .pdf.")


def _load_backlog(backlog_path: str) -> list[dict]:
    try:
        with open(backlog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Backlog file is not valid JSON: {e}", param_hint="--backlog")

    if not isinstance(data, list):
        raise click.BadParameter("Backlog JSON must be a list of objects.", param_hint="--backlog")

    return data


@click.command()
@click.option("--notes", required=True, type=click.Path(exists=True), help="Meeting notes file (.txt, .md, or .pdf)")
@click.option("--backlog", required=True, type=click.Path(exists=True), help="Existing backlog (.json list)")
@click.option("--output", default="user_stories.json", show_default=True, help="Output file path")
@click.option("--verbose", is_flag=True, help="Show step-by-step pipeline progress")
def main(notes, backlog, output, verbose):
    """Smart Backlog Assistant — turns meeting notes into structured user stories."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo("Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.", err=True)
        sys.exit(1)

    # Parse inputs
    try:
        parser = _select_parser(notes)
        notes_text = parser.parse(notes)
    except ValueError as e:
        click.echo(f"Error reading notes file: {e}", err=True)
        sys.exit(1)

    if not notes_text.strip():
        click.echo("Error: Notes file is empty.", err=True)
        sys.exit(1)

    existing_backlog = _load_backlog(backlog)

    if verbose:
        click.echo(f"\nProcessing: {notes}")
        click.echo(f"Backlog items loaded: {len(existing_backlog)}")
        click.echo(f"Notes length: {len(notes_text.split())} words\n")

    # Run pipeline
    try:
        result = pipeline.run(notes_text, existing_backlog, verbose=verbose)
    except anthropic.AuthenticationError:
        click.echo("Error: Invalid ANTHROPIC_API_KEY. Check your .env file.", err=True)
        sys.exit(1)
    except anthropic.APITimeoutError:
        click.echo("Error: API request timed out after retries. Try again.", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Pipeline error: {e}", err=True)
        sys.exit(1)

    # Write output
    formatter.write_output(result, output, source_file=notes)


if __name__ == "__main__":
    main()
