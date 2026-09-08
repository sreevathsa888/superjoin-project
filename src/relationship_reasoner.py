"""Hybrid deterministic-first relationship classification."""
from __future__ import annotations

from .models import ComparisonResult, Fact, RelationshipLabel
from .normalizer import NormalizedValue, normalize_value, values_equivalent
from .utils import json_loads_lenient


class RelationshipReasoner:
    def __init__(self, api_key: str | None = None, model: str = "openai/gpt-oss-120b") -> None:
        self.model = model
        self.client = None
        if api_key:
            from groq import Groq
            self.client = Groq(api_key=api_key)

    def classify(self, a: Fact, b: Fact) -> ComparisonResult:
        context = self._context_differences(a, b)
        norm_a, norm_b = normalize_value(a.value, a.unit), normalize_value(b.value, b.unit)
        if a.confidence < 0.60 or b.confidence < 0.60:
            return ComparisonResult(relationship=RelationshipLabel.UNCERTAIN, confidence=0.75, reason="At least one extracted fact has low confidence and requires human review before comparison.", context_differences=context)
        if context:
            return ComparisonResult(relationship=RelationshipLabel.CONTEXTUALIZED, confidence=0.88, reason=f"The claims differ in context ({'; '.join(context)}), so they can both be true.", context_differences=context)
        if values_equivalent(norm_a, norm_b):
            return ComparisonResult(relationship=RelationshipLabel.CORROBORATED, confidence=0.94, reason="The claims have aligned context and equivalent normalized values.")
        if self._comparable_values(norm_a, norm_b):
            return ComparisonResult(relationship=RelationshipLabel.CONTRADICTION, confidence=0.86, reason="The claims concern aligned context but their normalized values conflict beyond rounding tolerance.")
        if self.client:
            return self._groq_judgment(a, b)
        return ComparisonResult(relationship=RelationshipLabel.UNCERTAIN, confidence=0.45, reason="Values could not be compared deterministically and Groq is not configured.")

    @staticmethod
    def _comparable_values(a: NormalizedValue, b: NormalizedValue) -> bool:
        return (a.numeric is not None and b.numeric is not None and a.unit == b.unit) or (a.kind == "text" and b.kind == "text" and a.value != b.value)

    @staticmethod
    def _context_differences(a: Fact, b: Fact) -> list[str]:
        result: list[str] = []
        for label, left, right in [("time", a.time or a.time_start, b.time or b.time_start), ("scope", a.scope, b.scope), ("location", a.location, b.location)]:
            if left and right and left.casefold().strip() != right.casefold().strip():
                result.append(f"different {label}: '{left}' vs '{right}'")
        return result

    def _groq_judgment(self, a: Fact, b: Fact) -> ComparisonResult:
        prompt = {"instruction": "Classify only same-subject, likely same-concept claims. Return JSON {relationship, confidence, reason, context_differences}. Labels: CORROBORATED, CONTRADICTION, CONTEXTUALIZED, UNCERTAIN, UNRELATED. Do not make external assumptions.", "fact_a": a.model_dump(mode="json", exclude={"created_at"}), "fact_b": b.model_dump(mode="json", exclude={"created_at"})}
        response = self.client.chat.completions.create(model=self.model, temperature=0, response_format={"type": "json_object"}, messages=[{"role": "user", "content": str(prompt)}])
        return ComparisonResult.model_validate(json_loads_lenient(response.choices[0].message.content or "{}"))

