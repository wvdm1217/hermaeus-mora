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
        typer.secho(
            "EDITOR environment variable not set. Falling back to inline prompt.",
            fg=typer.colors.YELLOW,
        )
        typer.echo(initial_content.strip())
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
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        typer.secho(f"Editor process failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
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
    updated_content = updated_content.rstrip() + "\n"

    if updated_content == initial_content:
        typer.secho("No changes detected. Skipping save.", fg=typer.colors.BLUE)
        return

    try:
        parsed_entry = storage.parse_markdown_string(updated_content)
        parsed_entry.metadata.updated_at = utc_now()
        storage.save_entry(parsed_entry)
        from hermaeus_mora.config import settings
        from hermaeus_mora.search import Indexer

        if settings.search.enabled:
            Indexer(settings.data_dir).index_entry(parsed_entry)
        typer.secho(
            f"Saved entry {parsed_entry.metadata.id} successfully.",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error saving entry: {e}", fg=typer.colors.RED, err=True)
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
        typer.secho("No entries found.", fg=typer.colors.YELLOW)
        return

    # Sort descending by updated_at or created_at (we'll use created_at)
    entries.sort(key=lambda e: e.metadata.created_at, reverse=True)
    entries = entries[:limit]

    # Simple text table
    typer.secho(
        f"{'ID':<5} | {'Date':<12} | {'Title':<30} | {'Tags':<20} | {'Slug'}",
        fg=typer.colors.CYAN,
        bold=True,
    )
    typer.echo("-" * 92)
    for entry in entries:
        dt_str = entry.metadata.created_at.strftime("%Y-%m-%d")
        title = entry.metadata.title or ""
        if len(title) > 27:
            title = title[:24] + "..."

        tags_str = ", ".join(entry.metadata.tags)
        if len(tags_str) > 17:
            tags_str = tags_str[:17] + "..."

        slug = entry.metadata.slug or ""
        if len(slug) > 30:
            slug = slug[:27] + "..."

        typer.echo(
            f"{entry.metadata.id:<5} | {dt_str:<12} | {title:<30} | "
            f"{tags_str:<20} | {slug}"
        )


@app.command()
def view(
    entry_id: int | None = typer.Argument(None, help="ID of the entry to view"),
) -> None:
    """View a journal entry."""
    if entry_id is None:
        entry = storage.get_latest_entry()
        if not entry:
            typer.secho("No entries to view.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
    else:
        entry = storage.get_entry(entry_id)
        if not entry:
            typer.secho(f"Entry with ID {entry_id} not found.", fg=typer.colors.RED)
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
            typer.secho("No entries to edit.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
    else:
        entry = storage.get_entry(entry_id)
        if not entry:
            typer.secho(f"Entry with ID {entry_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)

    initial_content = storage.format_markdown_file(entry)
    updated_content = open_editor(initial_content)
    updated_content = updated_content.rstrip() + "\n"

    if updated_content == initial_content:
        typer.secho("No changes detected. Skipping save.", fg=typer.colors.BLUE)
        return

    try:
        parsed_entry = storage.parse_markdown_string(updated_content)
        # Ensure we keep the same ID unless user intentionally broke it,
        # but we should enforce ID
        if parsed_entry.metadata.id != entry.metadata.id:
            typer.secho(
                "Warning: ID was changed in frontmatter. Reverting ID to original.",
                fg=typer.colors.YELLOW,
            )
            parsed_entry.metadata.id = entry.metadata.id

        parsed_entry.metadata.updated_at = utc_now()
        storage.save_entry(parsed_entry)
        from hermaeus_mora.config import settings
        from hermaeus_mora.search import Indexer

        if settings.search.enabled:
            Indexer(settings.data_dir).index_entry(parsed_entry)
        typer.secho(
            f"Updated entry {parsed_entry.metadata.id} successfully.",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error updating entry: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e


@app.command()
def rm(entry_id: int = typer.Argument(..., help="ID of the entry to remove")) -> None:
    """Delete a journal entry."""
    entry = storage.get_entry(entry_id)
    if not entry:
        typer.secho(f"Entry with ID {entry_id} not found.", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.confirm(f"Are you sure you want to delete entry {entry_id}?", abort=True)
    if storage.delete_entry(entry_id):
        from hermaeus_mora.config import settings
        from hermaeus_mora.search import Indexer

        if settings.search.enabled:
            Indexer(settings.data_dir).delete_entry(str(entry_id))
        typer.secho(f"Deleted entry {entry_id}.", fg=typer.colors.GREEN)
    else:
        typer.secho(f"Failed to delete entry {entry_id}.", fg=typer.colors.RED)


@app.command()
def index() -> None:
    """Rebuild the search index for all entries."""
    from hermaeus_mora.config import settings
    from hermaeus_mora.search import Indexer

    if not settings.search.enabled:
        typer.secho("Search is disabled in config.", fg=typer.colors.YELLOW)
        return

    typer.secho("Building search index...", fg=typer.colors.CYAN)

    try:
        indexer = Indexer(settings.data_dir)
        indexer.index_all()
        typer.secho("Search index rebuilt successfully.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error building index: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, help="Maximum number of results to return"),
) -> None:
    """Search entries using full-text and semantic search."""
    from hermaeus_mora.config import settings
    from hermaeus_mora.search import Indexer

    if not settings.search.enabled:
        typer.secho("Search is disabled in config.", fg=typer.colors.YELLOW)
        return

    try:
        indexer = Indexer(settings.data_dir)
        results = indexer.search(query)

        if not results:
            typer.secho("No results found.", fg=typer.colors.YELLOW)
            return

        results = results[:limit]

        typer.secho(
            f"{'ID':<5} | {'Score':<6} | {'Path'}",
            fg=typer.colors.CYAN,
            bold=True,
        )
        typer.echo("-" * 50)

        for r in results:
            score_str = f"{r['score']:.2f}"
            typer.echo(f"{r['memory_id']:<5} | {score_str:<6} | {r['file_path']}")

    except Exception as e:
        typer.secho(f"Error during search: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
