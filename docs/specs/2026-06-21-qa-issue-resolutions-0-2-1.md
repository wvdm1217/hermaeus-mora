---
title: "0.2.1 QA Issue Resolutions"
author: "wvdm1217"
date: "2026-06-21"
version: "0.2.1"
status: "Implemented"
---

# 0.2.1 QA Issue Resolutions

## 1. Overview
This specification addresses five distinct issues identified during the quality assurance (QA) testing of the `hermaeus-mora` CLI (`hm`). These issues range from critical data loss due to filename collisions to minor visual formatting bugs in the CLI output. Resolving these will stabilize the v0.2.1 release.

## 2. Motivation & Goals
- **Why are we doing this?**
  To prevent data loss, ensure a smooth user experience when environmental variables (like `$EDITOR`) are missing or fail, optimize disk I/O, and maintain clean visual output in the terminal.
- **Goals:**
  - Eliminate the possibility of overwriting older entries when titles/slugs collide on the same date.
  - Handle editor process failures gracefully without showing Python tracebacks to the user.
  - Prevent redundant disk writes and `updated_at` changes if an entry is opened but unmodified, standardizing trailing newlines.
  - Ensure the `hm ls` command table does not break visually when entries have excessively long slugs.
  - Enhance the overall CLI visual aesthetics using `typer`'s native styling features (`typer.style`, `typer.colors`, etc.) rather than importing `rich` directly.
- **Non-Goals:**
  - Completely redesigning the storage mechanism or metadata schema.
  - Implementing a full-blown interactive terminal UI (TUI) as the fallback editor.

## 3. Architecture & Design
These changes fit within the existing CLI (`cli.py`), Storage (`storage.py`), and Configuration (`config.py`) modules.
- **Components involved:**
  - `storage.py`: Filename generation (`new`) and update logic (`edit`).
  - `cli.py`: Fallback editor prompt, subprocess execution, list formatting.
- **Data flow:**
  - When saving an entry, the filename must incorporate a uniqueness constraint (e.g., the unique ID).
  - When editing, the entry's raw text must be compared against the post-edit text before proceeding with a save.
- **Dependencies:**
  - `subprocess`, `typer` for handling the editor and CLI prompts.

## 4. Implementation Details
- **Data structures & models:**
  - No new fields added to the YAML frontmatter. The existing `id` field will be leveraged for unique filename generation if needed.
- **Core Logic / Algorithms:**
  1. **Filename Collision (storage.py):** Change the filename generation to `<date>_<id>_<slug>.md`. The slug portion should be limited to whole words totaling under 15 characters. Only truncate a word mid-string if the single word itself exceeds 15 characters. Keep whole words until adding the next word would exceed 15 characters.
  2. **Fallback Editor (cli.py):** Do not prompt the user about metadata restrictions. The Markdown file is just a file and can be freely edited by the user. Remove any artificial barriers or warnings in the fallback path.
  3. **Editor Failure (cli.py):** Wrap `subprocess.run(..., check=True)` in a `try...except subprocess.CalledProcessError:` block. On exception, print a clean error and call `raise typer.Exit(1)`.
  4. **Redundant Updates (cli.py / storage.py):** Normalize entries to always have exactly *one* trailing newline. After the editor closes, normalize the new content. If the normalized `original_content == new_content`, exit early without updating `updated_at` or writing to disk.
  5. **Table Formatting (cli.py):** In `hm ls`, apply truncation to the `slug` variable at a strict 30-character limit to preserve visual structure.
  6. **CLI Aesthetics (cli.py):** Leverage `typer.echo` and `typer.style` (or `typer.secho`) to beautify the CLI output. Add color coding for errors/success messages and improve terminal formatting without adding a direct `rich` dependency.

## 5. Testing & Edge Cases
- **Unit Tests:**
  - Test filename generation with duplicate slugs on the same date, ensuring the `<date>_<id>_<slug>.md` format and 15-character word-aware slug truncation.
  - Test redundant update prevention, including cases where only trailing newlines differ.
  - Test `hm ls` formatting with a 100-character slug, ensuring 30-character truncation.
  - Test aesthetic rendering elements to ensure they don't break stdout pipelines (e.g., when piped to another command).
- **Integration Tests:**
  - Run the CLI with a broken `$EDITOR` command and assert the exit code and error message.
- **Edge Cases & Failure Modes:**
  - Existing files named `<date>_<slug>.md` without IDs. The system must still be able to load these (storage reads should parse all `.md` files in the directory regardless of exact naming convention, as long as they parse correctly).
  - Highly concurrent writes (not typically a problem for a personal CLI, but unique IDs help avoid race conditions on file creation).

## 6. Observability & Reliability
- **Logs:** Log when a redundant write is skipped. Log fallback editor usage.
- **Metrics / Dashboards:** N/A for local CLI.
- **Alerts:** N/A.

## 7. Rollout & Rollback
- **Feature Flags:** None required.
- **Deployment Steps:** Included in the `0.2.1` release tag.
- **Rollback Plan:** Revert the commits if the unique filename logic breaks backward compatibility with the user's existing markdown files.

## 8. Changelog
- *2026-06-21*: Initial Draft - wvdm1217
