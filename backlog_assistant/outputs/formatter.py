import json
from datetime import datetime

import click


def write_output(result: dict, output_path: str, source_file: str = "") -> None:
    """Write full result to JSON and print a readable summary to stdout."""
    _write_json(result, output_path, source_file)
    _print_summary(result, output_path)


def _write_json(result: dict, output_path: str, source_file: str) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(),
        "source_file": source_file,
        "summary": result["summary"],
        "stats": result["stats"],
        "stories": result["stories"],
        "duplicates_skipped": result["duplicates"],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _print_summary(result: dict, output_path: str) -> None:
    stats = result["stats"]
    stories = result["stories"]
    duplicates = result["duplicates"]

    _divider()
    click.echo("SMART BACKLOG ASSISTANT — RESULTS")
    _divider()

    if result["summary"]:
        click.echo(f"\n{result['summary']}\n")

    click.echo(f"  Requirements found : {stats['requirements_found']}")
    click.echo(f"  New requirements   : {stats['new_requirements']}")
    click.echo(f"  Duplicates skipped : {stats['duplicates_found']}")
    click.echo(f"  Stories generated  : {stats['stories_generated']}")
    click.echo(f"  Stories refined    : {stats['issues_refined']}")

    if stories:
        _divider()
        click.echo("GENERATED STORIES")
        _divider()
        for i, story in enumerate(stories, 1):
            priority = story.get("priority", "?").upper()
            complexity = story.get("estimated_complexity", "?")
            category = story.get("category", "?")
            click.echo(f"\n  {i}. [{priority}] {story.get('title', 'Untitled')}")
            click.echo(f"     As a {story.get('as_a', '?')},")
            click.echo(f"     I want {story.get('i_want', '?')},")
            click.echo(f"     so that {story.get('so_that', '?')}")
            click.echo(f"     Category: {category}  |  Complexity: {complexity}")
            click.echo("     Acceptance criteria:")
            for ac in story.get("acceptance_criteria", []):
                click.echo(f"       - {ac}")

    if duplicates:
        _divider()
        click.echo("SKIPPED — already in backlog")
        _divider()
        for dup in duplicates:
            click.echo(f"  - {dup.get('requirement', '?')}")
            click.echo(f"    matched: {dup.get('matched_item', '?')}")

    _divider()
    click.echo(f"Output written to: {output_path}")
    _divider()


def _divider():
    click.echo("\n" + "-" * 60)
