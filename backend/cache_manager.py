# backend/cache_manager.py
"""
Semantic cache using SQLite.
Avoids redundant Pinecone queries and Groq calls.
Cache hit = instant response, zero API cost.
"""

import sqlite3, json, hashlib, time, os
import numpy as np
from sentence_transformers import SentenceTransformer

CACHE_DB   = os.path.join(os.path.dirname(__file__), "aura_cache.db")
SIMILARITY_THRESHOLD = 0.92   # cosine sim above this = cache hit
CACHE_TTL  = 60 * 60 * 24 * 7  # 7 days in seconds

class CacheManager:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vibe_cache (
                    id          TEXT PRIMARY KEY,
                    query_text  TEXT NOT NULL,
                    vector_blob BLOB NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at  REAL NOT NULL,
                    hit_count   INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS narrative_cache (
                    id          TEXT PRIMARY KEY,
                    cache_key   TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at  REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created
                ON vibe_cache(created_at)
            """)
            conn.commit()

    # ── Vibe/match cache ───────────────────────────────────────────────────

    def get_vibe(self, movie_overview: str, mbti: str, persona: str) -> dict | None:
        """
        Check if we've seen a semantically similar query before.
        Returns cached matches if cosine similarity > threshold.
        """
        query_vec = self.model.encode([movie_overview], normalize_embeddings=True)[0]
        now = time.time()

        with sqlite3.connect(CACHE_DB) as conn:
            rows = conn.execute("""
                SELECT id, query_text, vector_blob, result_json, created_at
                FROM vibe_cache
                WHERE created_at > ?
                ORDER BY created_at DESC
                LIMIT 200
            """, (now - CACHE_TTL,)).fetchall()

        for row in rows:
            cached_vec = np.frombuffer(row[2], dtype=np.float32)
            sim = float(np.dot(query_vec, cached_vec))
            if sim >= SIMILARITY_THRESHOLD:
                # Update hit count
                with sqlite3.connect(CACHE_DB) as conn:
                    conn.execute(
                        "UPDATE vibe_cache SET hit_count = hit_count + 1 WHERE id = ?",
                        (row[0],)
                    )
                result = json.loads(row[3])
                result["_cache_hit"]  = True
                result["_cache_sim"]  = round(sim * 100, 1)
                result["_cache_query"] = row[1]
                print(f"  [Cache HIT] sim={sim:.3f} for '{row[1][:40]}'")
                return result

        return None

    def set_vibe(self, movie_overview: str, result: dict):
        """Store a vibe match result in cache."""
        vec = self.model.encode([movie_overview], normalize_embeddings=True)[0]
        cache_id = hashlib.md5(movie_overview.encode()).hexdigest()

        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO vibe_cache
                    (id, query_text, vector_blob, result_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cache_id,
                movie_overview[:200],
                vec.astype(np.float32).tobytes(),
                json.dumps(result),
                time.time()
            ))
            conn.commit()

    # ── Narrative cache ────────────────────────────────────────────────────

    def get_narrative(self, location_name: str, movie: str, mbti: str) -> dict | None:
        key = hashlib.md5(f"{location_name}|{movie}|{mbti}".encode()).hexdigest()
        with sqlite3.connect(CACHE_DB) as conn:
            row = conn.execute("""
                SELECT result_json FROM narrative_cache
                WHERE id = ? AND created_at > ?
            """, (key, time.time() - CACHE_TTL)).fetchone()
        if row:
            print(f"  [Narrative cache HIT] {location_name} + {movie}")
            return json.loads(row[0])
        return None

    def set_narrative(self, location_name: str, movie: str, mbti: str, result: dict):
        key = hashlib.md5(f"{location_name}|{movie}|{mbti}".encode()).hexdigest()
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO narrative_cache
                    (id, cache_key, result_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (key, f"{location_name}|{movie}|{mbti}",
                  json.dumps(result), time.time()))
            conn.commit()

    # ── Stats ──────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        with sqlite3.connect(CACHE_DB) as conn:
            vibe_count = conn.execute(
                "SELECT COUNT(*), SUM(hit_count) FROM vibe_cache"
            ).fetchone()
            narr_count = conn.execute(
                "SELECT COUNT(*) FROM narrative_cache"
            ).fetchone()
        return {
            "vibe_entries":   vibe_count[0] or 0,
            "total_hits":     vibe_count[1] or 0,
            "narrative_entries": narr_count[0] or 0,
        }

    def clear_expired(self):
        """Run this in a background thread periodically."""
        cutoff = time.time() - CACHE_TTL
        with sqlite3.connect(CACHE_DB) as conn:
            deleted = conn.execute(
                "DELETE FROM vibe_cache WHERE created_at < ?", (cutoff,)
            ).rowcount
            conn.execute(
                "DELETE FROM narrative_cache WHERE created_at < ?", (cutoff,)
            )
            conn.commit()
        print(f"Cache cleanup: removed {deleted} expired entries")