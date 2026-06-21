import abc
import contextlib
import time
from pathlib import Path

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine

from hermaeus_mora import storage
from hermaeus_mora.config import settings
from hermaeus_mora.models import Entry


class Memory(SQLModel, table=True):
    __tablename__ = "memories"

    memory_id: str = Field(primary_key=True)
    file_path: str
    content: str


class BaseEmbedder(abc.ABC):
    @abc.abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        pass


class OllamaEmbedder(BaseEmbedder):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "ollama package is not installed. "
                "Please install it with `uv add ollama`"
            ) from None

        embeddings = []
        for content in texts:
            resp = ollama.embeddings(model=self.model_name, prompt=content)
            embeddings.append(resp["embedding"])
        return embeddings


class DuckDBStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.engine = create_engine(f"duckdb:///{self.db_path}")
        self._init_db()

    def _init_db(self) -> None:
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.exec(  # type: ignore
                text("INSTALL fts; LOAD fts;")
            )
            session.exec(  # type: ignore
                text("INSTALL vss; LOAD vss;")
            )

            with contextlib.suppress(Exception):
                session.exec(  # type: ignore
                    text("ALTER TABLE memories ADD COLUMN embedding FLOAT[];")
                )

            with contextlib.suppress(Exception):
                session.exec(  # type: ignore
                    text(
                        "PRAGMA create_fts_index("
                        "'memories', 'memory_id', 'content', 'file_path'"
                        ")"
                    )
                )

            session.commit()

    def upsert_memory(
        self,
        memory_id: str,
        file_path: str,
        content: str,
        embedding: list[float] | None = None,
    ) -> None:
        with self._get_session() as session:
            existing = session.get(Memory, memory_id)
            if existing:
                existing.file_path = file_path
                existing.content = content
                session.add(existing)
            else:
                new_mem = Memory(
                    memory_id=memory_id, file_path=file_path, content=content
                )
                session.add(new_mem)
            session.commit()

            if embedding is not None:
                session.exec(  # type: ignore
                    text(
                        "UPDATE memories SET embedding = :emb WHERE memory_id = :mem_id"
                    ),
                    params={"emb": embedding, "mem_id": memory_id},
                )
                session.commit()

    def refresh_fts_index(self) -> None:
        with self._get_session() as session:
            with contextlib.suppress(Exception):
                session.exec(  # type: ignore
                    text("PRAGMA drop_fts_index('memories')")
                )
            session.exec(  # type: ignore
                text(
                    "PRAGMA create_fts_index("
                    "'memories', 'memory_id', 'content', 'file_path'"
                    ")"
                )
            )
            session.commit()

    def delete_memory(self, memory_id: str) -> None:
        with self._get_session() as session:
            existing = session.get(Memory, memory_id)
            if existing:
                session.delete(existing)
                session.commit()

    def _get_session(self) -> Session:
        max_retries = 5
        base_delay = 0.1
        for attempt in range(max_retries):
            try:
                session = Session(self.engine)
                session.exec(  # type: ignore
                    text("SELECT 1")
                )
                return session
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Failed to acquire DuckDB lock after {max_retries} "
                        f"attempts: {e}"
                    ) from e
                time.sleep(base_delay * (2**attempt))
        raise RuntimeError("Unreachable")

    def search(
        self,
        query: str,
        alpha: float = 0.5,
        limit: int = 10,
        query_embedding: list[float] | None = None,
    ) -> list[dict]:
        with self._get_session() as session:
            if query_embedding and settings.search.vector_enabled:
                sql = f"""
                WITH bm25_scores AS (
                    SELECT memory_id,
                           fts_main_memories.match_bm25(memory_id, :query) AS bm25
                    FROM memories
                    WHERE fts_main_memories.match_bm25(memory_id, :query) IS NOT NULL
                ),
                vector_scores AS (
                    SELECT memory_id,
                           array_cosine_similarity(
                               CAST(embedding AS FLOAT[{len(query_embedding)}]),
                               CAST(:q_emb AS FLOAT[{len(query_embedding)}])
                           ) AS cosine
                    FROM memories
                    WHERE embedding IS NOT NULL
                )
                SELECT
                    m.memory_id,
                    m.file_path,
                    COALESCE(b.bm25, 0) AS bm25_score,
                    COALESCE(v.cosine, 0) AS cosine_score
                FROM memories m
                LEFT JOIN bm25_scores b ON m.memory_id = b.memory_id
                LEFT JOIN vector_scores v ON m.memory_id = v.memory_id
                WHERE b.bm25 IS NOT NULL OR v.cosine IS NOT NULL
                """
                res = session.exec(  # type: ignore
                    text(sql), params={"query": query, "q_emb": query_embedding}
                ).fetchall()

                results = []
                max_bm25 = max([r[2] for r in res]) if res else 1.0
                if max_bm25 == 0:
                    max_bm25 = 1.0

                for r in res:
                    norm_bm25 = r[2] / max_bm25
                    hybrid_score = (alpha * norm_bm25) + ((1 - alpha) * r[3])
                    results.append(
                        {"memory_id": r[0], "file_path": r[1], "score": hybrid_score}
                    )

                results.sort(key=lambda x: x["score"], reverse=True)
                return results[:limit]
            else:
                sql = """
                SELECT memory_id, file_path,
                       fts_main_memories.match_bm25(memory_id, :query) AS score
                FROM memories
                WHERE fts_main_memories.match_bm25(memory_id, :query) IS NOT NULL
                ORDER BY score DESC
                LIMIT :limit
                """
                res = session.exec(  # type: ignore
                    text(sql), params={"query": query, "limit": limit}
                ).fetchall()
                return [
                    {"memory_id": r[0], "file_path": r[1], "score": r[2]} for r in res
                ]


class Indexer:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.db_path = self.data_dir / "search.duckdb"
        self.store = DuckDBStore(self.db_path)
        self.embedder = self._get_embedder()

    def _get_embedder(self) -> BaseEmbedder | None:
        if not settings.search.vector_enabled:
            return None
        if settings.search.provider == "ollama":
            return OllamaEmbedder(settings.search.embedding_model)
        raise ValueError(f"Unknown embedding provider: {settings.search.provider}")

    def _upsert_single_entry(self, entry: Entry) -> None:
        embedding = None
        if self.embedder and entry.content.strip():
            try:
                embedding = self.embedder.get_embeddings([entry.content])[0]
            except Exception as e:
                print(f"Failed to embed entry {entry.metadata.id}: {e}")

        self.store.upsert_memory(
            memory_id=str(entry.metadata.id),
            file_path=str(storage.get_entry_path(entry).name),
            content=entry.content,
            embedding=embedding,
        )

    def index_all(self) -> None:
        entries = storage.get_all_entries()
        for entry in entries:
            self._upsert_single_entry(entry)

        self.store.refresh_fts_index()

    def search(self, query: str) -> list[dict]:
        query_embedding = None
        if self.embedder:
            try:
                query_embedding = self.embedder.get_embeddings([query])[0]
            except Exception as e:
                print(f"Failed to embed query: {e}")

        return self.store.search(query=query, query_embedding=query_embedding)

    def index_entry(self, entry: Entry) -> None:
        self._upsert_single_entry(entry)
        self.store.refresh_fts_index()

    def delete_entry(self, memory_id: str) -> None:
        self.store.delete_memory(memory_id)
        self.store.refresh_fts_index()
