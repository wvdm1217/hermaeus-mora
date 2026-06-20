from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class EntryMetadata(BaseModel):
    id: int
    title: str | None = None
    slug: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    summary: str | None = None
    source: str | None = None
    importance: int | None = Field(default=None, ge=1, le=10)
    context: str | None = None

    @field_validator("tags", "links", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v: Any) -> list[str]:
        return v if v is not None else []


class Entry(BaseModel):
    metadata: EntryMetadata
    content: str
