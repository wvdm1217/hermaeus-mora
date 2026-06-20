import os
import shlex
import subprocess
import tempfile

import typer

from hermaeus_mora import storage
from hermaeus_mora.models import Entry, EntryMetadata, utc_now

app = typer.Typer(invoke_without_command=True, help="Journal Entry CLI (hm)")


def open_editor(initial_content: str) -> str:
    editor = os.environ.get("EDITOR")
    if not editor:
        typer.echo(
            "EDITOR environment variable not set. Falling back to inline prompt."
        )
        # If fallback, we extract frontmatter and just prompt for body
        # For simplicity, we just ask for the body and append it to initial_content
        print("---")
        print(initial_content.strip())
        print("---")
        body = typer.prompt("Enter your journal entry content")
        return f"{initial_content}\n{body}\n"

    with tempfile.NamedTemporaryFile(
        suffix=".md", mode="w+", encoding="utf-8", delete=False
    ) as tf:
        tf.write(initial_content)
        tf.flush()
        filepath = tf.name

    try:
        editor_cmd = shlex.split(editor)
        subprocess.run([*editor_cmd, filepath], check=True)
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    finally:
        os.remove(filepath)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    Journal Entry CLI for managing markdown-based entries.
    """
    if ctx.invoked_subcommand is None:
        new(title=None)


@app.command()
def new(
    title: str | None = typer.Option(None, help="Optional title for the entry"),
) -> None:
    """Create a new journal entry."""
    if not title:
        title = typer.prompt("Title (optional)", default="", show_default=False)
        if not title:
            title = None

    slug = storage.generate_slug(title)
    entry_id = storage.get_next_id()

    metadata = EntryMetadata(id=entry_id, title=title, slug=slug)
    # The default content might just be a newline so it's ready to type
    entry = Entry(metadata=metadata, content="\n")

    initial_content = storage.format_markdown_file(entry)
    updated_content = open_editor(initial_content)

    try:
        parsed_entry = storage.parse_markdown_string(updated_content)
        parsed_entry.metadata.updated_at = utc_now()
        storage.save_entry(parsed_entry)
        typer.echo(f"Saved entry {parsed_entry.metadata.id} successfully.")
    except Exception as e:
        typer.echo(f"Error saving entry: {e}", err=True)
        raise typer.Exit(1) from e


@app.command("ls")
@app.command("list")
def list_entries(
    limit: int = typer.Option(10, help="Number of entries to show"),
    tag: str | None = typer.Option(None, help="Filter by tag (case-insensitive)"),
) -> None:
    """List recent journal entries."""
    entries = storage.get_all_entries()

    if tag:
        entries = [
            e for e in entries if any(t.lower() == tag.lower() for t in e.metadata.tags)
        ]

    if not entries:
        typer.echo("No entries found.")
        return

    # Sort descending by updated_at or created_at (we'll use created_at)
    entries.sort(key=lambda e: e.metadata.created_at, reverse=True)
    entries = entries[:limit]

    # Simple text table
    typer.echo(f"{'ID':<5} | {'Date':<12} | {'Title':<30} | {'Slug'}")
    typer.echo("-" * 70)
    for entry in entries:
        dt_str = entry.metadata.created_at.strftime("%Y-%m-%d")
        title = entry.metadata.title or ""
        if len(title) > 27:
            title = title[:24] + "..."
        slug = entry.metadata.slug or ""
        typer.echo(f"{entry.metadata.id:<5} | {dt_str:<12} | {title:<30} | {slug}")


@app.command()
def view(
    entry_id: int | None = typer.Argument(None, help="ID of the entry to view"),
) -> None:
    """View a journal entry."""
    if entry_id is None:
        entry = storage.get_latest_entry()
        if not entry:
            typer.echo("No entries to view.")
            raise typer.Exit(1)
    else:
        entry = storage.get_entry(entry_id)
        if not entry:
            typer.echo(f"Entry with ID {entry_id} not found.")
            raise typer.Exit(1)

    typer.echo(storage.format_markdown_file(entry))


@app.command()
def edit(
    entry_id: int | None = typer.Argument(None, help="ID of the entry to edit"),
) -> None:
    """Edit an existing journal entry."""
    if entry_id is None:
        entry = storage.get_latest_entry()
        if not entry:
            typer.echo("No entries to edit.")
            raise typer.Exit(1)
    else:
        entry = storage.get_entry(entry_id)
        if not entry:
            typer.echo(f"Entry with ID {entry_id} not found.")
            raise typer.Exit(1)

    initial_content = storage.format_markdown_file(entry)
    updated_content = open_editor(initial_content)

    try:
        parsed_entry = storage.parse_markdown_string(updated_content)
        # Ensure we keep the same ID unless user intentionally broke it,
        # but we should enforce ID
        if parsed_entry.metadata.id != entry.metadata.id:
            typer.echo(
                "Warning: ID was changed in frontmatter. Reverting ID to original."
            )
            parsed_entry.metadata.id = entry.metadata.id

        parsed_entry.metadata.updated_at = utc_now()
        storage.save_entry(parsed_entry)
        typer.echo(f"Updated entry {parsed_entry.metadata.id} successfully.")
    except Exception as e:
        typer.echo(f"Error updating entry: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def rm(entry_id: int = typer.Argument(..., help="ID of the entry to remove")) -> None:
    """Delete a journal entry."""
    entry = storage.get_entry(entry_id)
    if not entry:
        typer.echo(f"Entry with ID {entry_id} not found.")
        raise typer.Exit(1)

    typer.confirm(f"Are you sure you want to delete entry {entry_id}?", abort=True)
    if storage.delete_entry(entry_id):
        typer.echo(f"Deleted entry {entry_id}.")
    else:
        typer.echo(f"Failed to delete entry {entry_id}.")
