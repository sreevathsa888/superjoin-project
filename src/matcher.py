"""Candidate retrieval that avoids an all-pairs comparison pass."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from .models import Fact


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.casefold()) if len(token) > 2}


def text_similarity(a: str, b: str) -> float:
    a_tokens, b_tokens = _tokens(a), _tokens(b)
    return len(a_tokens & b_tokens) / max(1, len(a_tokens | b_tokens))


@dataclass(frozen=True)
class CandidatePair:
    fact_a: Fact
    fact_b: Fact
    score: float


class CandidateMatcher:
    """Lightweight hashed-token embedding candidate retrieval, with transparent scores.

    It deliberately narrows candidates only. Final semantic equivalence is decided by the reasoner.
    """
    def __init__(self, min_score: float = 0.24) -> None:
        self.min_score = min_score

    def find_candidates(self, new_facts: list[Fact], existing_facts: list[Fact]) -> list[CandidatePair]:
        buckets: dict[str, list[Fact]] = defaultdict(list)
        for fact in existing_facts:
            for token in _tokens(f"{fact.subject} {fact.predicate}"):
                buckets[token].append(fact)
        pairs: list[CandidatePair] = []
        seen: set[tuple[str, str]] = set()
        for fact in new_facts:
            # Low-confidence/ambiguous extractions are retained for review, not amplified into noisy links.
            if fact.needs_review:
                continue
            possible = {other.fact_id: other for token in _tokens(f"{fact.subject} {fact.predicate}") for other in buckets.get(token, [])}
            for other in possible.values():
                if other.needs_review:
                    continue
                if other.document_id == fact.document_id:
                    continue
                key = tuple(sorted((fact.fact_id, other.fact_id)))
                if key in seen:
                    continue
                seen.add(key)
                subject = text_similarity(fact.subject, other.subject)
                predicate = text_similarity(fact.predicate, other.predicate)
                type_bonus = 0.10 if fact.value_type == other.value_type else 0
                score = 0.45 * subject + 0.45 * predicate + type_bonus
                if score >= self.min_score:
                    pairs.append(CandidatePair(fact, other, score))
        return sorted(pairs, key=lambda pair: pair.score, reverse=True)
