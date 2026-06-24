---
title: "Incremental Indexing and Performance Measurement"
author: "Werner van der Merwe"
date: "2026-06-21"
version: "0.3.1"
status: "Draft"
---

# Incremental Indexing and Performance Measurement

## 1. Overview
The current indexing process in `hermaeus-mora` processes every entry and generates embeddings unconditionally, even if the file content hasn't changed. This is computationally expensive, slow, and may lead to rate limiting from embedding providers. This spec proposes adding a `content_hash` column to the index to track the state of indexed documents. By hashing the embedding model, provider, and document content, the indexer can skip the embedding and database write steps for files that haven't changed. Additionally, we will measure and log the indexing time to monitor these performance improvements.

## 2. Motivation & Goals
- **Why are we doing this?** Re-embedding unmodified text wastes time and provider API quotas.
- **Goals:**
  - Introduce a stable content hash derived from `(provider, model, content)`.
  - Avoid re-embedding and re-indexing if the hash hasn't changed.
  - Measure and report the time taken to run the indexer.
- **Non-Goals:**
  - Altering the hybrid search algorithms.
  - Deleting unused entries from the database (garbage collection is out of scope for this particular spec).

## 3. Architecture & Design
- **Components involved:**
  - `src/hermaeus_mora/search.py`: Specifically the `Memory` model, `DuckDBStore`, and `Indexer`.
  - `src/hermaeus_mora/cli.py`: To output the total indexing time.
- **Data flow:**
  1. `Indexer.index_all()` iterates through entries and times the entire operation.
  2. For each entry, `Indexer` computes `sha256(f"{provider}:{model}:{content}")`.
  3. `DuckDBStore` exposes a method to check the existing hash for a given `memory_id`, or `upsert_memory` handles it efficiently. Since `OllamaEmbedder.get_embeddings` is slow, the hash check must occur *before* requesting embeddings.
  4. If the hash matches, skip the embedding step and optionally the database upsert entirely.
  5. If the hash differs (or is new), fetch the embedding and upsert to DuckDB, updating the `content_hash`.
- **Dependencies:** Built-in `hashlib` and `time` modules.

## 4. Implementation Details
- **Decisions on Edge Cases:**
  - **Embedding failures:** If embedding generation fails, we will explicitly *not* update the `content_hash` in DuckDB. This ensures that the file is picked up for re-indexing on the subsequent run.
  - **Version Invalidation:** The hash will strictly be `(provider, model, content)`. Upgrades to `hermaeus-mora` won't implicitly invalidate hashes unless the model/provider changes or content is updated.
  - **Output Formatting:** `typer.secho` will be used for displaying the standard performance metrics as requested, showcasing the before/after performance dynamically.

- **Data structures & models:**
  - `search.py::Memory`: Add `content_hash: str | None = Field(default=None)`.
  - `search.py::DuckDBStore._init_db()`: Add schema migration step:
    ```sql
    ALTER TABLE memories ADD COLUMN content_hash VARCHAR;
    ```
    (Wrapped in `contextlib.suppress(Exception)` for backward compatibility).
- **Core Logic / Algorithms:**
  - In `Indexer._upsert_single_entry`:
    ```python
    def _upsert_single_entry(self, entry: Entry) -> bool:
        provider = settings.search.provider
        model = settings.search.embedding_model
        # Use hashlib.sha256
        content_hash = generate_hash(provider, model, entry.content)

        existing_hash = self.store.get_content_hash(str(entry.metadata.id))
        if existing_hash == content_hash:
            return False # Skipped

        # Proceed with embedding and upsert
        ...
        self.store.upsert_memory(..., content_hash=content_hash)
        return True # Indexed
    ```
  - In `Indexer.index_all()`:
    ```python
    def index_all(self) -> None:
        start_time = time.perf_counter()
        entries = storage.get_all_entries()
        updated_count = 0
        skipped_count = 0
        for entry in entries:
            if self._upsert_single_entry(entry):
                updated_count += 1
            else:
                skipped_count += 1

        self.store.refresh_fts_index()
        end_time = time.perf_counter()
        print(f"Indexing complete in {end_time - start_time:.2f}s. Updated: {updated_count}, Skipped: {skipped_count}")
    ```
- **API Contracts:** The `hm search index` command will now print a summary of how many files were updated, skipped, and the total time taken.

## 5. Testing & Edge Cases
- **Unit Tests:**
  - Verify that the `content_hash` generation is deterministic.
  - Test `DuckDBStore` correctly stores and retrieves the `content_hash`.
  - Test `Indexer._upsert_single_entry` skips embedding if the hash matches.
- **Integration Tests:**
  - Run the CLI command `hm search index` twice. The first run should update all files and take time > 0. The second run should update 0 files, skip all, and take significantly less time.
- **Edge Cases & Failure Modes:**
  - Missing `content_hash` column in older databases: Handled by the `ALTER TABLE` execution block on startup.
  - Provider or Model change: Will naturally trigger a re-index because `provider` and `model` are parts of the hash string.
  - Embedding failure: If the embedder raises an exception, we must ensure we don't accidentally update the `content_hash` to the new one if the embedding wasn't successfully saved, leaving the database in an inconsistent state.

## 6. Observability & Reliability
- **Logs:** Print summary statistics (Time taken, Updated, Skipped).
- **Metrics / Dashboards:** Rely on CLI stdout for current scope.
- **Alerts:** None for local usage.

## 7. Rollout & Rollback
- **Feature Flags:** None required.
- **Deployment Steps:** Applied seamlessly on next CLI run. The DuckDB initialization sequence handles the column addition automatically.
- **Rollback Plan:** Removing the hashing logic will still leave the `content_hash` column in DuckDB, which is harmless.

## 8. Changelog
- *2026-06-21*: Initial Draft - Werner van der Merwe
