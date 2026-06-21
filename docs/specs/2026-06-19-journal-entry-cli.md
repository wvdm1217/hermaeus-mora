---
title: "Journal Entry CLI (hm)"
author: "Werner van der Merwe"
date: "2026-06-19"
version: "0.1.0"
status: "Implemented"
---

# Journal Entry CLI (hm)

## 1. Overview
The initial implementation of the `hermaeus-mora` system focuses on the foundational data generation loop. This specification details the creation of a CLI tool, exposed via the `hm` entrypoint, designed to handle basic Create, Read, Update, and Delete (CRUD) operations for personal journal entries. These entries will be stored as Markdown files with YAML frontmatter to hold structured metadata, similar to the experience provided by tools like `jrnl`.

## 2. Motivation & Goals
- **Why are we doing this?** To establish the core mechanism for users to input and manage their memories locally before introducing complex LLM and agentic workflows. A frictionless, local-first editing experience is crucial.
- **Goals:**
  - Build a project-level CLI using `typer`.
  - Provide strict, explicit, and Pythonic configuration using `pydantic` and `pydantic_settings`.
  - Store all entries as Markdown files dumped into a local `data/` directory. Files will be named using a `YYYY-MM-DD_<slug>.md` convention.
  - Automatically manage YAML frontmatter metadata (e.g., `created_at`, `updated_at`, `id`, `slug`, and basic statistics) for each entry.
  - Enable fast CRUD commands via the terminal.
- **Non-Goals:**
  - LLM integration or text summarization.
  - Vector database or external knowledge graph synchronization.
  - Graphical or web-based UI.

## 3. Architecture & Design
The architecture is kept explicit, relying on standard, modern Python ecosystem tools.
- **Components involved:**
  - **`cli.py`**: Defines the Typer application and command routing.
  - **`config.py`**: Manages application settings (e.g., data directory path) using `pydantic_settings`.
  - **`models.py`**: Pydantic models for the YAML frontmatter and internal entry representations.
  - **`storage.py`**: Handles filesystem operations (reading, writing, deleting) and Markdown/frontmatter parsing.
- **Data flow:**
  1. The user executes an `hm` command in the terminal.
  2. Typer routes the command and initializes the settings from `config.py`.
  3. The `storage` module is called to interact with the Markdown files in the `data/` directory.
  4. If editing or creating, the user's default system `$EDITOR` is invoked. If `$EDITOR` is missing, the CLI falls back to accepting text input directly via a `typer.prompt`.
  5. Upon saving and closing the editor (or submitting the prompt), `storage.py` updates the `updated_at` metadata and persists the file.
- **Dependencies:**
  - `typer` (CLI framework)
  - `pydantic` (Data modeling and validation)
  - `pydantic-settings` (Configuration management)
  - `python-frontmatter` or a similarly explicit YAML parsing approach to separate metadata from Markdown body.

## 4. Implementation Details
- **Data structures & models:**
  ```python
  from pydantic import BaseModel, Field
  from datetime import datetime

  class EntryMetadata(BaseModel):
      id: int
      title: str | None = None
      slug: str | None = None
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
      # Future: tags, links, word_count, etc.
  ```

  ```python
  from pydantic_settings import BaseSettings, SettingsConfigDict
  from pathlib import Path

  class Settings(BaseSettings):
      data_dir: Path = Path("data")

      model_config = SettingsConfigDict(
          env_prefix="hm_",
          env_file=".env",
          env_file_encoding="utf-8"
      )
  ```
- **Core Logic / Algorithms:**
  - **Create (`hm new` / `hm`)**: Prompt the user for an optional title to generate a slug. Determine the next sequential integer ID (starting from 0). Create a temporary file with default frontmatter. Open it in `$EDITOR` (or fallback to an inline text prompt if `$EDITOR` is not set). Once complete, validate the frontmatter, format it, and move it to `data/YYYY-MM-DD_<slug>.md`.
  - **Read (`hm list` / `hm ls`)**: Iterate through `data/*.md`, parse frontmatter, and display a formatted table of entries. By default, this should scale by limiting the output to the most recent 10 entries sorted by `created_at` or `updated_at`.
  - **Read Single (`hm view [id]`)**: Print the rendered or raw markdown of a specific entry to the terminal. If `[id]` is omitted, default to the most recently created entry.
  - **Update (`hm edit [id]`)**: Open the specified file in `$EDITOR`. If `[id]` is omitted, default to editing the most recently created entry. Upon closing, update the `updated_at` field and save.
  - **Delete (`hm rm <id>`)**: Permanently remove the file from the filesystem after a confirmation prompt.
- **API Contracts:**
  - `hm`: Defaults to `hm new`.
  - `hm ls`: Lists entries.
  - `hm view [id]`: Views an entry (defaults to the latest).
  - `hm edit [id]`: Edits an entry (defaults to the latest).
  - `hm rm <id>`: Deletes an entry.

## 5. Testing & Edge Cases
- **Unit Tests:**
  - `test_config.py`: Ensure settings load correctly and respect environment variable overrides (`HM_DATA_DIR`).
  - `test_storage.py`: Test reading and writing frontmatter, ensuring no data loss when modifying the Markdown body.
  - `test_models.py`: Validate Pydantic model serialization and deserialization of datetimes.
- **Integration Tests:**
  - Use `typer.testing.CliRunner` to simulate CLI commands in an isolated temporary directory. Verify that `hm new` creates a file and `hm ls` discovers it.
- **Edge Cases & Failure Modes:**
  - The `data/` directory doesn't exist (ensure application auto-creates it).
  - Malformed YAML frontmatter by the user (catch parsing errors and display a helpful message; do not overwrite data).
  - Environment variable `$EDITOR` is missing (fallback to `typer.prompt` for inline text input).
  - Attempting to edit or delete a non-existent entry ID.

## 6. Observability & Reliability
- **Logs:**
  - Minimal local logging. Use Typer's `echo` for user-facing errors.
  - Debug logs can be implemented later or managed via a `--verbose` flag.
- **Metrics / Dashboards:** N/A for a local CLI tool.
- **Alerts:** N/A.

## 7. Rollout & Rollback
- **Feature Flags:** None required.
- **Deployment Steps:**
  - Add the `typer` app to the `[project.scripts]` section in `pyproject.toml` so `uv` installs it globally as `hm`.
  - Example: `hm = "hermaeus_mora.cli:app"`
- **Rollback Plan:**
  - As this is the foundational commit, a standard Git revert is sufficient.

## 8. Changelog
- *2026-06-19*: Initial Draft - Werner van der Merwe
