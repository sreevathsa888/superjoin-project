from src.models import Fact, RelationshipLabel
from src.relationship_reasoner import RelationshipReasoner


def fact(value: str, *, time: str | None = "FY2024", scope: str | None = "company", confidence: float = 0.9) -> Fact:
    return Fact(document_id=value + (time or ""), source_document="source.pdf", source_page=1, source_chunk=value + "chunk", subject="Acme", predicate="revenue", value=value, value_type="number", unit="USD", time=time, scope=scope, evidence=f"Acme revenue was {value}.", confidence=confidence)


def test_corroboration_after_normalization():
    assert RelationshipReasoner().classify(fact("$10M"), fact("USD 10,000,000")).relationship == RelationshipLabel.CORROBORATED


def test_genuine_numeric_contradiction():
    assert RelationshipReasoner().classify(fact("$10M"), fact("$15M")).relationship == RelationshipLabel.CONTRADICTION


def test_different_time_is_contextualized():
    assert RelationshipReasoner().classify(fact("$10M", time="FY2023"), fact("$15M", time="FY2024")).relationship == RelationshipLabel.CONTEXTUALIZED


def test_low_confidence_is_uncertain():
    assert RelationshipReasoner().classify(fact("$10M", confidence=0.3), fact("$10M")).relationship == RelationshipLabel.UNCERTAIN
