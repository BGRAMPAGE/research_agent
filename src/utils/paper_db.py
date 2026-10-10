"""Local RAG retrieval over a curated arXiv paper-chunk corpus (Postgres + pgvector)."""
import ast
import logging
import threading
import time
from typing import List, Dict, Optional

from src.config import config  # must come BEFORE sentence_transformers (loads .env)

from psycopg2 import pool as pg_pool
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def format_authors(authors, max_names: int = 3) -> str:
    """Authors can arrive as a list, a nested list, or a stringified list."""
    if isinstance(authors, str):
        try:
            authors = ast.literal_eval(authors)
        except (ValueError, SyntaxError):
            return authors

    def flatten(items):
        for item in items:
            if isinstance(item, (list, tuple)):
                yield from flatten(item)
            else:
                yield str(item)

    names = list(flatten(authors)) if isinstance(authors, (list, tuple)) else [str(authors)]
    if len(names) > max_names:
        return ", ".join(names[:max_names]) + " et al."
    return ", ".join(names)

class PaperRetriever:
    """Retrieves semantically similar paper chunks from a Postgres+pgvector database.

    The embedding model is loaded LAZILY (on first .search() call, not at __init__)
    so importing this module / starting the app doesn't pay the multi-second,
    ~2GB model load cost unless the RAG feature is actually used in a given session.

    All methods here are SYNCHRONOUS/BLOCKING (DB I/O + CPU-bound embedding).
    Callers in async code (e.g. tools.py) MUST wrap calls in asyncio.to_thread().
    """

    def __init__(self, db_config: dict, model_name: str = "BAAI/bge-m3"):
        self.db_config = db_config
        self.model_name = model_name
        self._embedding_model: Optional[SentenceTransformer] = None
        self._model_lock = threading.Lock()

        # Pooled connections instead of one connect/close per search.
        self._pool = pg_pool.ThreadedConnectionPool(minconn=1, maxconn=5, **db_config)

    @property
    def embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            with self._model_lock:
                if self._embedding_model is None:  # re-check inside lock
                    logger.info(f"Loading embedding model '{self.model_name}' (first use)...")
                    self._embedding_model = SentenceTransformer(self.model_name)
                    logger.info("Embedding model loaded.")
        return self._embedding_model

    def embed_query(self, query: str) -> list:
        embedding = self.embedding_model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.embed_query(query)
        connection = self._pool.getconn()
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT
                        pc.chunk_id, pc.paper_id, p.title, p.authors,
                        p.source_url, pc.chunk_index, pc.content,
                        1 - (pc.embedding <=> %s::vector) AS similarity
                    FROM paper_chunks pc
                    JOIN papers p ON p.paper_id = pc.paper_id
                    WHERE pc.embedding IS NOT NULL
                    ORDER BY pc.embedding <=> %s::vector
                    LIMIT %s;
                """
                cursor.execute(sql, (query_embedding, query_embedding, top_k))
                rows = cursor.fetchall()
                return [
                    {
                        "chunk_id": row[0], "paper_id": row[1], "title": row[2],
                        "authors": row[3], "source_url": row[4], "chunk_index": row[5],
                        "content": row[6], "similarity": float(row[7]),
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Paper DB search failed: {e}")
            return []
        finally:
            self._pool.putconn(connection)

    def close(self):
        self._pool.closeall()


class ContextBuilder:
    """Formats retrieved chunks into a structured context block."""

    def build(self, results: List[Dict]) -> str:
        context_parts = []
        for i, result in enumerate(results, 1):
            source = f"""SOURCE {i}
Paper: {result['title']}
Authors: {format_authors(result['authors'])}
Paper ID: {result['paper_id']}
Chunk: {result['chunk_index']}
Similarity: {result['similarity']:.4f}

Content:
{result['content']}""".strip()
            context_parts.append(source)
        return "\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# Module-level singleton: created lazily, reused across every tool call and
# the RAG page. Fails gracefully to None if the DB is unreachable — the rest
# of the app must keep working without this feature in that case.
# ---------------------------------------------------------------------------
_retriever_instance: Optional[PaperRetriever] = None
_context_builder = ContextBuilder()


_last_init_failure: float = 0.0
_INIT_RETRY_COOLDOWN_SECONDS = 60


def get_paper_retriever() -> Optional[PaperRetriever]:
    """Shared PaperRetriever, or None if RAG is disabled or the DB is unreachable.
    After a failed connect, skips retrying for 60s so a down DB can't stall every call."""
    global _retriever_instance, _last_init_failure

    if not config.rag_enabled:
        return None

    if _retriever_instance is None:
        if time.time() - _last_init_failure < _INIT_RETRY_COOLDOWN_SECONDS:
            return None
        try:
            _retriever_instance = PaperRetriever(
                db_config={
                    "dbname": config.rag_db_name,
                    "user": config.rag_db_user,
                    "password": config.rag_db_password,
                    "host": config.rag_db_host,
                    "port": config.rag_db_port,
                    "connect_timeout": 5,
                },
                model_name=config.rag_embedding_model,
            )
        except Exception as e:
            _last_init_failure = time.time()
            logger.error(f"Paper DB unreachable, retrying in {_INIT_RETRY_COOLDOWN_SECONDS}s: {e}")
            return None

    return _retriever_instance


def get_context_builder() -> ContextBuilder:
    return _context_builder