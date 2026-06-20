from datetime import UTC, datetime

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class EntryMetadata(BaseModel):
    id: int
    title: str | None = None
    slug: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Entry(BaseModel):
    metadata: EntryMetadata
    content: str
