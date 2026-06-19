from datetime import UTC, datetime

from hermaeus_mora.models import EntryMetadata


def test_metadata_defaults():
    metadata = EntryMetadata(id=1)
    assert metadata.id == 1
    assert metadata.title is None
    assert metadata.slug is None
    assert isinstance(metadata.created_at, datetime)
    assert metadata.created_at.tzinfo == UTC


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
