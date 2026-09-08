"""SQLite persistence with normalized document, chunk, fact, and relationship tables."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from .chunker import Chunk
from .models import Fact, Relationship


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS documents (document_id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE, page_count INTEGER NOT NULL, status TEXT NOT NULL, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS chunks (chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id), page_number INTEGER NOT NULL, text TEXT NOT NULL, is_table_like INTEGER NOT NULL, note TEXT);
            CREATE TABLE IF NOT EXISTS facts (fact_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id), source_document TEXT NOT NULL, source_page INTEGER NOT NULL, source_chunk TEXT NOT NULL REFERENCES chunks(chunk_id), subject TEXT NOT NULL, predicate TEXT NOT NULL, value TEXT NOT NULL, value_type TEXT NOT NULL, normalized_value TEXT, unit TEXT, normalized_unit TEXT, time TEXT, time_start TEXT, time_end TEXT, scope TEXT, location TEXT, qualifiers TEXT NOT NULL, evidence TEXT NOT NULL, confidence REAL NOT NULL, extraction_notes TEXT, needs_review INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS relationships (relationship_id TEXT PRIMARY KEY, fact_a_id TEXT NOT NULL REFERENCES facts(fact_id), fact_b_id TEXT NOT NULL REFERENCES facts(fact_id), relationship TEXT NOT NULL, confidence REAL NOT NULL, reason TEXT NOT NULL, context_differences TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(fact_a_id, fact_b_id));
            """)

    def find_document_by_hash(self, sha256: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute("SELECT * FROM documents WHERE sha256 = ?", (sha256,)).fetchone()

    def add_document(self, filename: str, sha256: str, page_count: int, status: str = "PROCESSING") -> str:
        document_id = str(uuid4())
        with self.connect() as db:
            db.execute("INSERT INTO documents(document_id, filename, sha256, page_count, status) VALUES (?, ?, ?, ?, ?)", (document_id, filename, sha256, page_count, status))
        return document_id

    def set_document_status(self, document_id: str, status: str, error: str | None = None) -> None:
        with self.connect() as db:
            db.execute("UPDATE documents SET status=?, error=? WHERE document_id=?", (status, error, document_id))

    def add_chunks(self, document_id: str, chunks: list[Chunk]) -> None:
        with self.connect() as db:
            db.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)", [(c.chunk_id, document_id, c.page_number, c.text, int(c.is_table_like), c.note) for c in chunks])

    def add_facts(self, facts: list[Fact]) -> None:
        with self.connect() as db:
            db.executemany("""INSERT INTO facts VALUES (:fact_id,:document_id,:source_document,:source_page,:source_chunk,:subject,:predicate,:value,:value_type,:normalized_value,:unit,:normalized_unit,:time,:time_start,:time_end,:scope,:location,:qualifiers,:evidence,:confidence,:extraction_notes,:needs_review,:created_at)""", [{**fact.model_dump(mode="json"), "value_type": fact.value_type.value, "qualifiers": json.dumps(fact.qualifiers), "needs_review": int(fact.needs_review)} for fact in facts])

    def add_relationships(self, relationships: list[Relationship]) -> None:
        with self.connect() as db:
            db.executemany("INSERT OR IGNORE INTO relationships VALUES (:relationship_id,:fact_a_id,:fact_b_id,:relationship,:confidence,:reason,:context_differences,:created_at)", [{**r.model_dump(mode="json"), "relationship": r.relationship.value, "context_differences": json.dumps(r.context_differences)} for r in relationships])

    def facts(self, document_id: str | None = None) -> list[Fact]:
        query, params = "SELECT * FROM facts", ()
        if document_id:
            query += " WHERE document_id=?"; params = (document_id,)
        with self.connect() as db:
            return [self._fact(row) for row in db.execute(query, params).fetchall()]

    def documents(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()]

    def relationships(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT r.*, fa.subject AS a_subject, fa.predicate AS a_predicate, fa.value AS a_value, fa.evidence AS a_evidence, fa.source_document AS a_document, fa.source_page AS a_page, fb.subject AS b_subject, fb.predicate AS b_predicate, fb.value AS b_value, fb.evidence AS b_evidence, fb.source_document AS b_document, fb.source_page AS b_page FROM relationships r JOIN facts fa ON r.fact_a_id=fa.fact_id JOIN facts fb ON r.fact_b_id=fb.fact_id ORDER BY r.created_at DESC").fetchall()]

    @staticmethod
    def _fact(row: sqlite3.Row) -> Fact:
        values = dict(row); values["qualifiers"] = json.loads(values["qualifiers"]); values["needs_review"] = bool(values["needs_review"])
        return Fact.model_validate(values)
