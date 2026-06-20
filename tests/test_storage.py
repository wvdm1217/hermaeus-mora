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
