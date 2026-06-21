---
title: "entry-tags"
author: "Werner van der Merwe"
date: "2026-06-20"
version: "0.2.0"
status: "Implemented"
---

# entry-tags

## 1. Overview
This specification details the expansion of the `EntryMetadata` schema in `hermaeus-mora` to include additional fields defined in the architecture, and the corresponding enhancement of the CLI to query and display this new metadata.

## 2. Motivation & Goals
- **Why are we doing this?**
  To align the implementation of `EntryMetadata` with the defined architectural vision, enabling richer semantic links, better categorization, and more powerful search and organization of memories.
- **Goals:**
  - Expand the `EntryMetadata` Pydantic model to include `tags` (list of strings), `links` (list of strings representing filenames), `summary` (string), `source` (string), `importance` (integer 1-10), and `context` (string).
  - Update the CLI `ls` command to support filtering by tags (e.g., `hm ls --tag "idea"`). Filtering should be case-insensitive.
  - Implement Pydantic validators to ensure null/omitted array fields (`tags`, `links`) are coerced into empty lists `[]`.
- **Non-Goals:**
  - Filtering by multiple tags simultaneously.
  - Implementing the actual vector database or knowledge graph synchronization.
  - Adding full-text search capabilities.

## 3. Architecture & Design
This feature expands the core data model of the application.
- **Components involved:**
  - `src/hermaeus_mora/models.py`: Updates to the `EntryMetadata` Pydantic model.
  - `src/hermaeus_mora/cli.py`: Enhancements to the `ls` command arguments to filter by tags, and potentially modifying the list output.
  - `src/hermaeus_mora/storage.py`: Exposing filtering or passing the load burden to the CLI. The easiest way is for `storage.py` to retrieve all entries, and the filtering is applied before returning them, or `cli.py` filters them after retrieval.
- **Data flow:**
  - User invokes `hm ls --tag "idea"`. The CLI retrieves all entries, filters them to include only those whose `tags` list contains `"idea"`, and then displays the results.
- **Dependencies:**
  - `pydantic` for model validation.
  - `typer` for CLI parameter handling.

## 4. Implementation Details
- **Data structures & models:**
  Modify `EntryMetadata` in `models.py`:
  ```python
  from pydantic import field_validator
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
      def coerce_none_to_list(cls, v):
          return v if v is not None else []
  ```
- **Core Logic / Algorithms:**
  - In `cli.py`, `list_entries` function will take an additional `tag: str | None = typer.Option(None, help="Filter by tag (case-insensitive)")`.
  - Filter logic: `if tag: entries = [e for e in entries if any(t.lower() == tag.lower() for t in e.metadata.tags)]`.
- **API Contracts:**
  - `hm ls [--tag <tag>] [--limit <limit>]`

## 5. Testing & Edge Cases
- **Unit Tests:**
  - Test serialization and deserialization of `EntryMetadata` with new fields (verify `yaml.dump` output structure).
  - Verify `importance` limits (validation error on `importance=11`).
  - Verify Pydantic validator correctly turns null/None into `[]` for `tags` and `links`.
  - Test `list_entries` filtering in the CLI via `typer.testing.CliRunner`, including case-insensitive matches.
- **Integration Tests:**
  - E2E tests for creating a note with tags, then querying with `--tag` (with different cases).
- **Edge Cases & Failure Modes:**
  - Empty or null tags in the YAML frontmatter. Pydantic validator will handle this by coercing to empty lists.
  - Case-insensitive filtering guarantees a smoother user experience, avoiding missing entries due to capitalization differences.

## 6. Observability & Reliability
- **Logs:**
  - Standard exception logging when loading a file fails due to validation errors.
- **Metrics / Dashboards:** N/A for local CLI.
- **Alerts:** N/A for local CLI.

## 7. Rollout & Rollback
- **Feature Flags:** None required.
- **Deployment Steps:** Included in regular package updates.
- **Rollback Plan:** Revert the changes to `models.py` and `cli.py`.

## 8. Changelog
- *2026-06-20*: Initial Draft - Werner van der Merwe
