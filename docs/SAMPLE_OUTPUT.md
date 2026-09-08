# Sample output shape

This is an illustrative generic output shape, not a preloaded fact and not a claim about the starter dataset.

```json
{
  "fact_id": "…",
  "subject": "Example organization",
  "predicate": "reported annual output",
  "value": "10 million",
  "value_type": "number",
  "unit": "USD",
  "time": "FY2024",
  "scope": "company",
  "normalized_value": "10000000",
  "normalized_unit": "USD",
  "source_document": "example.pdf",
  "source_page": 4,
  "source_chunk": "…",
  "evidence": "Annual output was USD 10 million in FY2024.",
  "confidence": 0.94,
  "needs_review": false
}
```

```json
{
  "relationship": "CORROBORATED",
  "confidence": 0.94,
  "reason": "The claims have aligned context and equivalent normalized values.",
  "context_differences": []
}
```

For a current, grounded result, run the app with `GROQ_API_KEY` configured and inspect its Evidence page. The app always exposes the actual quote, document, and page before the relationship is presented.
