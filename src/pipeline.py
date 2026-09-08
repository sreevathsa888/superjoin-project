"""Orchestration for incremental, fault-tolerant document processing."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .chunker import chunk_pages
from .config import Settings
from .database import Database
from .fact_extractor import build_extractor
from .matcher import CandidateMatcher
from .models import Fact, Relationship
from .normalizer import normalize_value
from .pdf_parser import extract_pdf_pages
from .relationship_reasoner import RelationshipReasoner
from .utils import logger


class FactKnowledgePipeline:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database, self.settings = database, settings
        self.extractor = build_extractor(settings.groq_api_key, settings.groq_model)
        self.matcher = CandidateMatcher()
        self.reasoner = RelationshipReasoner(settings.groq_api_key, settings.groq_model)

    def process_pdf(self, path: str | Path) -> dict:
        path = Path(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        duplicate = self.database.find_document_by_hash(digest)
        if duplicate:
            return {"status": "duplicate", "document_id": duplicate["document_id"], "filename": path.name, "facts": 0, "relationships": 0}
        pages = extract_pdf_pages(path, self.settings.max_pages_per_document)
        document_id = self.database.add_document(path.name, digest, len(pages))
        try:
            logger.info("Processing document: %s", path.name)
            chunks = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
            self.database.add_chunks(document_id, chunks)
            facts: list[Fact] = []
            for chunk in chunks:
                try:
                    result = self.extractor.extract(chunk)
                    for candidate in result.facts:
                        normalized = normalize_value(candidate.value, candidate.unit)
                        facts.append(Fact(**candidate.model_dump(), document_id=document_id, source_document=path.name, source_page=chunk.page_number, source_chunk=chunk.chunk_id, normalized_value=normalized.value, normalized_unit=normalized.unit, needs_review=candidate.confidence < self.settings.low_confidence_threshold or bool(candidate.extraction_notes)))
                except Exception as error:
                    logger.warning("Chunk %s extraction failed: %s", chunk.chunk_id, error)
            self.database.add_facts(facts)
            existing = [fact for fact in self.database.facts() if fact.document_id != document_id]
            candidates = self.matcher.find_candidates(facts, existing)
            relationships = [Relationship(fact_a_id=pair.fact_a.fact_id, fact_b_id=pair.fact_b.fact_id, **self.reasoner.classify(pair.fact_a, pair.fact_b).model_dump()) for pair in candidates]
            self.database.add_relationships(relationships)
            self.database.set_document_status(document_id, "COMPLETE")
            logger.info("Extracted %s facts and classified %s relationships", len(facts), len(relationships))
            return {"status": "complete", "document_id": document_id, "filename": path.name, "facts": len(facts), "relationships": len(relationships)}
        except Exception as error:
            self.database.set_document_status(document_id, "FAILED", str(error))
            logger.error("Failed to process document %s: %s", path.name, error)
            raise
