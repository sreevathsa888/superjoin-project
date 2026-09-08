from pydantic import ValidationError
import pytest
from src.models import FactCandidate


def test_fact_requires_evidence():
    with pytest.raises(ValidationError):
        FactCandidate(subject="A", predicate="has", value="1", evidence="", confidence=0.9)


def test_generic_fact_supports_textual_claim():
    fact = FactCandidate(subject="Research team", predicate="reported status", value="complete", value_type="text", evidence="The research team reported status complete.", confidence=0.8)
    assert fact.value_type == "text"
