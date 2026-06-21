---
title: "Full-Text and Vector Search (Discoverability) via DuckDB"
author: "Werner van der Merwe"
date: "2026-06-21"
version: "0.3.0"
status: "Draft"
---

# Full-Text and Vector Search (Discoverability) via DuckDB

## 1. Overview
This specification details the implementation of full-text and semantic (vector) search for the Hermaeus Mora memory system. By leveraging DuckDB and its extensions (`fts` and `vss`), we will provide a hybrid search functionality that allows users to seamlessly retrieve memory files (Markdown) based on both exact keyword matches and underlying semantic meaning. A new `hm index` command will generate the local database state, and `hm search <query>` will allow CLI-based lookup similar to `grep`.

## 2. Motivation & Goals
- **Why are we doing this?** The architecture mandates that memories must be highly discoverable. As the number of raw Markdown files grows, retrieving entries solely by ID or listing them becomes ineffective. Users need a powerful, unified search mechanism.
- **Goals:**
  - Implement a hybrid search combining Full-Text Search (DuckDB FTS) and Semantic Search (DuckDB VSS / vector embeddings).
  - Add an `hm index` CLI command to build/rebuild the DuckDB state.
  - Add an `hm search <query>` CLI command to retrieve relevant files efficiently.
  - Make the vector store heavily config-driven and isolate the embedding model logic to easily support alternative third-party models in the future.
  - Embed the entire Markdown file content (no chunking for now).
  - Automatically index new files upon creation or update.
- **Non-Goals:**
  - Complex chunking strategies for long documents (deferred to future iterations).
  - A graphical user interface for search.

## 3. Architecture & Design
The system will introduce DuckDB as an embedded analytical data store that tracks metadata, full-text tokens, and vector embeddings for each Markdown memory.
- **Components involved:**
  - **Storage Layer (Markdown):** The source of truth remains the Markdown files.
  - **Index Manager (`hermaeus_mora.search.Indexer`):** Handles scanning files, building the DuckDB database, and parsing metadata.
  - **Embedding Provider Interface:** An abstract base class defining `embed(text: str) -> List[float]`. By default, this will use local [Ollama](https://ollama.com/) with a specified model (e.g., `embeddinggemma`). The provider and model will be fully config-driven to allow swapping to other third-party models.
  - **DuckDB Database:** Stores memory IDs, paths, text content, and embeddings. Leverages the `fts` and `vss` extensions.
  - **CLI Layer (`hermaeus_mora.cli`):** Exposes `index` and `search` subcommands.
- **Data flow:**
  1. `hm index` or standard CLI actions (like `hm new` or `hm edit`) trigger the Index Manager to update the relevant records.
  2. Index Manager reads the Markdown file, extracts content, and passes it to the Embedding Provider.
  3. The Embedding Provider returns the vector embedding.
  4. Index Manager upserts the record (path, text, embedding) into DuckDB and updates the FTS index.
  5. `hm search <query>` queries DuckDB using a hybrid scoring algorithm (combining `bm25` score and `cosine_similarity` score).

## 4. Implementation Details
- **Data structures & models:**
  - Introduce schemas using `sqlmodel`:
    ```python
    from sqlmodel import SQLModel, Field
    from typing import List, Optional

    class Memory(SQLModel, table=True):
        __tablename__ = "memories"

        memory_id: str = Field(primary_key=True)
        file_path: str
        content: str
        # Conceptually maps to DuckDB's FLOAT[384] array.
        # May require custom SQLAlchemy type mapping depending on duckdb-engine support.
        embedding: Optional[List[float]] = None
    ```
- **Core Logic / Algorithms:**
  - **Indexing:** Iterate over all Markdown files. If `hm index` is run, process all files. If a CLI command modifies/adds a file, trigger a targeted upsert. The file's content is embedded as a single string.
  - **DuckDB Extensions:** On database initialization, execute `INSTALL fts; LOAD fts; INSTALL vss; LOAD vss;` relying on an internet connection for the first run.
  - **Concurrency:** Because DuckDB is a single-writer system, database connection acquisition for writes will include a retry mechanism with an exponential backoff limit to handle simultaneous CLI command executions gracefully (first-come, first-serve).
  - **Search Algorithm:**
    - Calculate BM25 score using DuckDB's `fts` extension.
    - If vector search is enabled (`config.search.vector_enabled = true`):
      - Calculate Cosine Similarity using DuckDB's `array_cosine_similarity` via the `vss` extension.
      - Normalize both scores using min-max normalization.
      - Compute a weighted hybrid score: `(alpha * norm_bm25) + ((1 - alpha) * cosine_sim)`.
    - If vector search is disabled, rely entirely on the BM25 score.
- **API Contracts:**
  - `Config`: Add `search` configurations, explicitly a `provider` (e.g., `"ollama"`) and an `embedding_model` (e.g., `"embeddinggemma"`).
  - `BaseEmbedder`: `def get_embeddings(texts: List[str]) -> List[List[float]]: pass`
  - `OllamaEmbedder`: Implements `BaseEmbedder` using the official `ollama` Python client.
  - `DuckDBStore`: Manages connections (via `sqlmodel` and `duckdb-engine`), schema initialization, `upsert_document`, and `search`.

## 5. Testing & Edge Cases
- **Unit Tests:**
  - Mock the Embedding Provider to ensure DuckDB ingestion and FTS logic work without network/heavy compute.
  - Verify configuration loading correctly instantiates the appropriate Embedding Provider.
  - Test hybrid score calculation logic with edge cases (e.g., exact matches scoring appropriately).
- **Integration Tests:**
  - End-to-end test of the `hm index` command generating a `.duckdb` file.
  - End-to-end test of `hm search` returning expected documents for known keywords.
- **Edge Cases & Failure Modes:**
  - Ollama daemon down or model missing -> provide a clear error message instructing the user to start Ollama or pull the model. Fall back to FTS only if acceptable.
  - Database locking issues with DuckDB during concurrent CLI executions -> managed via the aforementioned backoff/retry limit; if it exceeds the limit, fail gracefully with an error.
  - Empty files or files with only frontmatter -> skip embedding or handle gracefully.

## 6. Observability & Reliability
- **Logs:**
  - Log indexing progress and total time taken.
  - Log failures during embedding generation.
  - Log search latency and the resulting top match IDs.
- **Metrics / Dashboards:** N/A for local CLI.
- **Alerts:** N/A for local CLI, but user-facing warnings should be clear if indexing fails.

## 7. Rollout & Rollback
- **Feature Flags:**
  - `config.search.enabled = true` (default): Toggles the entire DuckDB search integration.
  - `config.search.vector_enabled = false` (default): Toggles vector embeddings and semantic search. When disabled, only full-text search (FTS) is used.
- **Deployment Steps:**
  - Update `pyproject.toml` to include `duckdb`, `duckdb-engine`, and `sqlmodel`.
  - Add `ollama` as an optional dependency group in `pyproject.toml` so it can be installed via `hermaeus-mora[ollama]`.
  - Roll out the new CLI commands.
- **Rollback Plan:**
  - Users can delete the `.duckdb` file and disable search in config if issues arise. No Markdown files will be altered or lost.

## 8. Changelog
- *2026-06-21*: Initial Draft - Werner van der Merwe
