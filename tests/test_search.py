from pathlib import Path
from unittest.mock import MagicMock

from hermaeus_mora.models import Entry, EntryMetadata
from hermaeus_mora.search import DuckDBStore, Indexer


def test_indexer_fts(tmp_path: Path):
    store = DuckDBStore(tmp_path / "test.duckdb")
    store.upsert_memory("1", "file1.md", "This is some content about spatialedge")
    store.upsert_memory("2", "file2.md", "This is some content about nothing")
    store.refresh_fts_index()

    results = store.search("spatialedge")
    assert len(results) == 1
    assert results[0]["memory_id"] == "1"


def test_embedder_disabled(tmp_path: Path):
    indexer = Indexer(tmp_path)
    # The default setting in tests might have vector_enabled as false
    # Just checking it doesn't crash
    indexer.index_entry(
        Entry(metadata=EntryMetadata(id=99, title="test"), content="content")
    )
    results = indexer.search("content")
    assert len(results) > 0


def test_embedder_enabled(tmp_path: Path, monkeypatch):
    from hermaeus_mora.config import settings

    monkeypatch.setattr(settings.search, "vector_enabled", True)

    indexer = Indexer(tmp_path)

    # Mock embedder
    mock_embedder = MagicMock()
    mock_embedder.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
    indexer.embedder = mock_embedder

    indexer.index_entry(
        Entry(
            metadata=EntryMetadata(id=100, title="test vector"),
            content="vector content",
        )
    )

    results = indexer.search("vector content")
    assert len(results) > 0
    assert results[0]["memory_id"] == "100"

    # Verify indexing all
    indexer.index_all()
    results = indexer.search("vector content")
    assert len(results) > 0


def test_duckdb_delete(tmp_path: Path):
    store = DuckDBStore(tmp_path / "test2.duckdb")
    store.upsert_memory("1", "file1.md", "This is some content")
    store.refresh_fts_index()
    results = store.search("content")
    assert len(results) == 1

    store.delete_memory("1")
    store.refresh_fts_index()
    results2 = store.search("content")
    assert len(results2) == 0


def test_indexer_delete_entry(tmp_path: Path):
    indexer = Indexer(tmp_path)
    indexer.index_entry(
        Entry(metadata=EntryMetadata(id=101, title="del"), content="delete me")
    )
    assert len(indexer.search("delete me")) == 1
    indexer.delete_entry("101")
    assert len(indexer.search("delete me")) == 0
