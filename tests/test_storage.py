from datetime import UTC, datetime

from hermaeus_mora import storage
from hermaeus_mora.models import Entry, EntryMetadata


def test_parse_markdown_file(tmp_path):
    content = """---
id: 1
title: Hello
slug: hello
created_at: '2026-06-19T12:00:00Z'
updated_at: '2026-06-19T12:00:00Z'
---
This is the body."""
    p = tmp_path / "test.md"
    p.write_text(content, encoding="utf-8")

    entry = storage.parse_markdown_file(p)
    assert entry.metadata.id == 1
    assert entry.metadata.title == "Hello"
    assert entry.content == "This is the body."
    assert entry.metadata.created_at == datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def test_format_markdown_file():
    dt = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    metadata = EntryMetadata(
        id=2, title="Test Format", slug="test-format", created_at=dt, updated_at=dt
    )
    entry = Entry(metadata=metadata, content="Body content\nmultiline")

    formatted = storage.format_markdown_file(entry)
    assert "id: 2" in formatted
    assert "title: Test Format" in formatted
    assert "---\nBody content" in formatted


def test_generate_slug():
    assert storage.generate_slug("Hello World!") == "hello-world"
    assert storage.generate_slug(None) == "untitled"
    assert storage.generate_slug("  Leading and Trailing -- ") == "leading-and-trailing"


def test_get_entry_path_truncation():
    dt = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    # Long slug that should be truncated word-aware to under 15
    metadata = EntryMetadata(
        id=42,
        title="Test Format",
        slug="this-is-a-very-long-slug",
        created_at=dt,
        updated_at=dt,
    )
    entry = Entry(metadata=metadata, content="body")
    path = storage.get_entry_path(entry)
    # "this-is-a-very" is 14 chars, adding "-long" would be 19.
    assert path.name == "2026-06-19_42_this-is-a-very.md"

    # Single word over 15 chars
    metadata = EntryMetadata(
        id=43,
        title="Super",
        slug="supercalifragilisticexpialidocious",
        created_at=dt,
        updated_at=dt,
    )
    entry = Entry(metadata=metadata, content="body")
    path = storage.get_entry_path(entry)
    assert path.name == "2026-06-19_43_supercalifragil.md"
