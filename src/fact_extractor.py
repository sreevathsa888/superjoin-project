"""Groq-backed structured extraction, isolated behind a small provider boundary."""
from __future__ import annotations

import re
from typing import Protocol

from .chunker import Chunk
from .models import ExtractionResult, FactCandidate
from .utils import json_loads_lenient, logger


EXTRACTION_SYSTEM_PROMPT = """You extract grounded, meaningful facts from a single PDF chunk. Return JSON only.
Do not infer missing values or use knowledge outside the chunk. JSON type rules: value must always be a quoted string; qualifiers must always be an object (use {} when absent); confidence must be a decimal number from 0.0 to 1.0, never words such as high; value_type must use only the listed values, and boolean claims should use text. Every fact must have an exact or near-exact evidence quote from this chunk.
Use generic subject/predicate/value fields that work for any domain. Capture time, scope, location, units and qualifiers only when explicit.
Skip boilerplate, table fragments with ambiguous label-value alignment, and irrelevant identifiers. If a table is ambiguous, either skip it or produce a low-confidence fact with extraction_notes explaining the ambiguity.
Return {\"facts\":[{subject,predicate,value,value_type,unit,time,time_start,time_end,scope,location,qualifiers,evidence,confidence,extraction_notes}],\"notes\":[...]}.
Valid value_type values: number, percentage, date, measurement, text, entity, event, relationship, other."""


class Extractor(Protocol):
    def extract(self, chunk: Chunk) -> ExtractionResult: ...


class GroqFactExtractor:
    def __init__(self, api_key: str, model: str) -> None:
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model

    def extract(self, chunk: Chunk) -> ExtractionResult:
        if not chunk.text:
            return ExtractionResult(notes=[chunk.note or "Empty extractable page; needs OCR."])
        hint = " This chunk looks table-like; only extract a row if the header-to-value association is unambiguous." if chunk.is_table_like else ""
        response = self.client.chat.completions.create(
            model=self.model, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": EXTRACTION_SYSTEM_PROMPT}, {"role": "user", "content": f"Page {chunk.page_number}.{hint}\n\n{chunk.text}"}],
        )
        payload = json_loads_lenient(response.choices[0].message.content or "{}")
        return ExtractionResult.model_validate(payload)


class RuleBasedFallbackExtractor:
    """Offline-safe extractor: finds only high-signal sentences with numbers and marks them for review."""
    def extract(self, chunk: Chunk) -> ExtractionResult:
        facts: list[FactCandidate] = []
        for sentence in re.split(r"(?<=[.!?])\s+", chunk.text):
            if re.search(r"\d", sentence) and len(sentence.split()) >= 4:
                facts.append(FactCandidate(subject="Unresolved subject", predicate="numeric statement", value="Unstructured numeric claim", value_type="other", evidence=sentence[:2400], confidence=0.35, extraction_notes="Groq is unavailable; human review is required."))
        return ExtractionResult(facts=facts[:12], notes=["Fallback extraction used; configure GROQ_API_KEY for structured facts."])


def build_extractor(api_key: str | None, model: str) -> Extractor:
    if api_key:
        return GroqFactExtractor(api_key, model)
    logger.warning("GROQ_API_KEY is not set; using intentionally low-confidence offline fallback.")
    return RuleBasedFallbackExtractor()

