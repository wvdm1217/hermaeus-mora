from pathlib import Path

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
