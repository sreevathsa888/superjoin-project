from src.matcher import CandidateMatcher
from src.models import Fact


def make_fact(doc: str, subject: str, predicate: str) -> Fact:
    return Fact(document_id=doc, source_document=f"{doc}.pdf", source_page=1, source_chunk=f"chunk-{doc}", subject=subject, predicate=predicate, value="10", value_type="number", evidence="Evidence says the value is 10.", confidence=0.9)


def test_matcher_finds_related_cross_document_facts():
    pairs = CandidateMatcher().find_candidates([make_fact("a", "Acme Corp", "annual revenue")], [make_fact("b", "Acme Corp", "revenue")])
    assert len(pairs) == 1


def test_matcher_skips_same_document_pairs():
    assert not CandidateMatcher().find_candidates([make_fact("a", "Acme", "revenue")], [make_fact("a", "Acme", "revenue")])
