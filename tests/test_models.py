from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from hermaeus_mora.models import EntryMetadata


def test_metadata_defaults():
    metadata = EntryMetadata(id=1)
    assert metadata.id == 1
    assert metadata.title is None
    assert metadata.slug is None
    assert isinstance(metadata.created_at, datetime)
    assert metadata.created_at.tzinfo == UTC
    assert metadata.tags == []
    assert metadata.links == []
    assert metadata.summary is None
    assert metadata.source is None
    assert metadata.importance is None
    assert metadata.context is None


def test_metadata_serialization():
    dt = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    metadata = EntryMetadata(
        id=2, title="Test", slug="test", created_at=dt, updated_at=dt
    )
    data = metadata.model_dump(mode="json")

    assert data["id"] == 2
    assert data["title"] == "Test"
    assert data["slug"] == "test"
    assert "2026-06-19T12:00:00Z" in data["created_at"]

    metadata_parsed = EntryMetadata(**data)
    assert metadata_parsed.created_at == dt


def test_metadata_new_fields_serialization():
    dt = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    metadata = EntryMetadata(
        id=3,
        title="Test Tags",
        slug="test-tags",
        created_at=dt,
        updated_at=dt,
        tags=["idea", "work"],
        links=["file1.md"],
        summary="summary here",
        source="book",
        importance=5,
        context="context string",
    )
    data = metadata.model_dump(mode="json")
    assert data["tags"] == ["idea", "work"]
    assert data["links"] == ["file1.md"]
    assert data["summary"] == "summary here"
    assert data["importance"] == 5

    parsed = EntryMetadata(**data)
    assert parsed.tags == ["idea", "work"]
    assert parsed.importance == 5


def test_metadata_importance_limits():
    with pytest.raises(ValidationError):
        EntryMetadata(id=4, importance=11)
    with pytest.raises(ValidationError):
        EntryMetadata(id=5, importance=0)

    # Valid
    m = EntryMetadata(id=6, importance=10)
    assert m.importance == 10
    m = EntryMetadata(id=7, importance=1)
    assert m.importance == 1


def test_metadata_list_coercion():
    data: dict[str, Any] = {"id": 8, "tags": None, "links": None}
    parsed = EntryMetadata(**data)
    assert parsed.tags == []
    assert parsed.links == []
