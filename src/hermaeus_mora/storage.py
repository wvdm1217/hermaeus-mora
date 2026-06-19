import re
from datetime import UTC
from pathlib import Path

import yaml

from hermaeus_mora.config import settings
from hermaeus_mora.models import Entry, EntryMetadata

FRONTMATTER_REGEX = re.compile(r"^---\n(.*?)\n---\n(.*)", re.DOTALL)


def ensure_data_dir() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)


def parse_markdown_file(path: Path) -> Entry:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_REGEX.match(content)
    if match:
        frontmatter_str = match.group(1)
        body = match.group(2)
        metadata_dict = yaml.safe_load(frontmatter_str) or {}
        metadata = EntryMetadata(**metadata_dict)
        return Entry(metadata=metadata, content=body)

    raise ValueError(f"No valid frontmatter found in {path}")


def format_markdown_file(entry: Entry) -> str:
    metadata_dict = entry.metadata.model_dump(mode="json")
    frontmatter = yaml.dump(metadata_dict, default_flow_style=False, sort_keys=False)
    # Ensure frontmatter doesn't have an extra trailing newline if it
    # already ends with one, but pyyaml dump typically ends with \n.
    return f"---\n{frontmatter}---\n{entry.content}"


def get_entry_path(entry: Entry) -> Path:
    # Use UTC date for consistent filename
    date_str = entry.metadata.created_at.astimezone(UTC).strftime("%Y-%m-%d")
    slug = entry.metadata.slug or f"entry-{entry.metadata.id}"
    filename = f"{date_str}_{slug}.md"
    return settings.data_dir / filename


def get_all_entries() -> list[Entry]:
    ensure_data_dir()
    entries = []
    for path in settings.data_dir.glob("*.md"):
        try:
            entries.append(parse_markdown_file(path))
        except Exception:
            # Skip invalid files for now
            continue
    return sorted(entries, key=lambda e: e.metadata.created_at)


def get_entry(entry_id: int) -> Entry | None:
    for entry in get_all_entries():
        if entry.metadata.id == entry_id:
            return entry
    return None


def get_latest_entry() -> Entry | None:
    entries = get_all_entries()
    if not entries:
        return None
    return entries[-1]


def save_entry(entry: Entry) -> None:
    ensure_data_dir()
    path = get_entry_path(entry)

    # If the file already exists but with a different name (e.g. if we update
    # something that changes the path), we should theoretically clean up the old
    # one, but for now we just write to the correct path. To handle ID uniqueness
    # and updates properly, we should find any existing file with this ID and
    # remove it if the path changed.
    for existing_path in settings.data_dir.glob("*.md"):
        try:
            existing_entry = parse_markdown_file(existing_path)
            if (
                existing_entry.metadata.id == entry.metadata.id
                and existing_path != path
            ):
                existing_path.unlink()
        except Exception:
            pass

    content = format_markdown_file(entry)
    path.write_text(content, encoding="utf-8")


def delete_entry(entry_id: int) -> bool:
    for path in settings.data_dir.glob("*.md"):
        try:
            entry = parse_markdown_file(path)
            if entry.metadata.id == entry_id:
                path.unlink()
                return True
        except Exception:
            pass
    return False


def get_next_id() -> int:
    entries = get_all_entries()
    if not entries:
        return 0
    return max(e.metadata.id for e in entries) + 1


def generate_slug(title: str | None) -> str:
    if not title:
        return "untitled"
    # Basic slugification
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")
