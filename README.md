# Fact Knowledge Layer

An evidence-first PDF fact comparison prototype for the Superjoin VIT 2026 assignment. It discovers generic facts in uploaded PDFs, grounds every accepted fact in its source page and quote, persists it, then identifies corroboration, contradiction, context-resolved differences, and uncertainty.

## Problem statement

Documents often state the same fact differently, disagree, or seem to disagree because their time, scope, location, unit, or definition differs. A useful fact layer must make those distinctions auditable rather than simply drawing a graph.

## Solution overview

`Streamlit -> PDF parser -> page-bounded chunks -> Groq structured extraction -> Pydantic validation -> normalization -> SQLite -> candidate retrieval -> context-aware reasoning -> evidence UI`

See [the architecture](docs/architecture.md) for the Mermaid diagram.

## Key features

- Multi-PDF upload and incremental ingestion; re-uploaded byte-identical PDFs are detected as duplicates.
- Generic Pydantic fact schema; no domain-specific fields or document rules.
- Evidence is mandatory and facts retain filename, document ID, page, chunk, quote, and confidence.
- Groq structured JSON extraction with a source-only, anti-hallucination prompt.
- Deterministic currency/scale/percentage/unit normalization and a documented 1.5% rounding tolerance.
- Candidate filtering before comparison, then deterministic context checks and Groq only for ambiguous semantic judgment.
- Explicit `CORROBORATED`, `CONTRADICTION`, `CONTEXTUALIZED`, `UNCERTAIN`, and `UNRELATED` labels.
- Review queue for empty/OCR-only pages, table ambiguity, low confidence, and offline fallback output.

## Tech stack

Python 3.11+, Streamlit, Groq, Pydantic, PyMuPDF with pypdf fallback, SQLite, a lightweight local candidate vector strategy, and pytest.

## Fact schema

Each fact has `subject`, `predicate`, `value`, `value_type`, optional `unit`, `time`, `time_start`, `time_end`, `scope`, `location`, and JSON `qualifiers`. It also has mandatory `evidence`, `confidence`, `document_id`, `source_document`, `source_page`, and `source_chunk`, plus normalized value/unit and review status. It supports numerical, textual, entity, event, date, percentage, measurement, and relationship claims.

## How extraction and grounding work

The application parses text one PDF page at a time and never creates chunks crossing page boundaries. Groq receives one chunk at a time and must return JSON. Pydantic validates the response. The extractor is told to return no fact without an evidence quote from that chunk, to avoid inferring, and to flag ambiguous tables. A missing Groq key triggers a deliberately low-confidence offline fallback so it never masquerades as a production extraction.

## Normalization, matching, and reasoning

`$10M`, `USD 10,000,000`, lakh/crore scales, percentages, and several physical units normalize into comparable values. Candidate retrieval uses an explainable local token-vector similarity over subject and predicate and only compares cross-document candidates. The relationship engine checks confidence first, then explicit time/scope/location differences, then normalized value equivalence. Only ambiguous comparisons call Groq for a source-constrained explanation.

## Four required cases

The UI labels outcomes as ✅ **CORROBORATED**, ❌ **CONTRADICTION**, ⚠️ **CONTEXTUALIZED**, and ❓ **UNCERTAIN**. The included test suite demonstrates all four generically; use the supplied PDFs in the UI to inspect real source quotes. The supplied set contains several useful starting points, such as overlapping Delhivery financial/operational disclosures across the prospectus, FY24 report, and Q4 presentation, differing historical time periods, and densely formatted tables that are deliberately sent to review when header-value mapping is not safe.

The exact facts shown depend on Groq extraction and should be verified in Evidence before presentation - this is intentional evidence-first behavior, not hard-coded demo output.

## Setup

```powershell
cd superjoin-fact-knowledge-layer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GROQ_API_KEY` to your Groq API key. `GROQ_MODEL` defaults to `openai/gpt-oss-120b`; change it to a Groq model available to your account if necessary. Never commit `.env`.

## Run

```powershell
streamlit run app.py
```

Open the displayed local URL, upload PDFs, process them, and inspect **Facts**, **Evidence**, **Relationships**, and **Review / Failures**.

## Testing

```powershell
pytest -q
```

Tests cover PDF empty-text handling, schema validation, currency/scale/percentage/unit normalization, candidate matching, corroboration, genuine contradiction, contextualized different-time claims, low-confidence uncertainty, and same-document matching exclusion.

The supplied archive has also been inspected in both logistics/financial and India macroeconomic domains. It is unpacked under `data/sample/` for upload through the UI, so both unrelated starter domains exercise the same generic pipeline. See [starter dataset notes](docs/STARTER_DATASET_NOTES.md) and [sample output shape](docs/SAMPLE_OUTPUT.md).

## API documentation

This intentionally uses a combined Streamlit application rather than a separate API because the assignment permits either and this keeps the prototype easy to run and explain. The service boundaries (`pipeline`, `database`, `fact_extractor`, and `relationship_reasoner`) make adding FastAPI endpoints straightforward without altering the core behavior.

## Engineering decisions and trade-offs

- **SQLite over graph DB:** document, chunk, fact, and relationship provenance are relational and small enough for a portable database. A graph visualization alone would not solve extraction or reasoning.
- **Local candidate vectors over an external embedding API:** this keeps the system usable with Groq-only credentials and avoids sending facts to another provider. It is a filter, not a semantic verdict; Groq handles ambiguous semantics.
- **Hybrid reasoning:** deterministic code handles arithmetic, tolerance, units, and obvious context; Groq does arbitrary-domain extraction and ambiguous textual comparison.
- **Streamlit over a custom frontend:** faster, transparent demonstration UI with no build step.

## Limitations and future work

Scanned PDFs need OCR; table detection is conservative and not a full layout model; entity resolution and synonym retrieval are modest; long documents still make one model call per chunk; and the UI does not yet render the original PDF page image. Production improvements would add OCR/layout extraction, a stronger local embedding model, human approval, semantic versioning, a vector index, provenance spans, and scalable storage.

## Project structure

```text
superjoin-fact-knowledge-layer/
  app.py                         # Streamlit interface
  src/                           # modular pipeline and services
  tests/                         # generic pytest suite
  data/sample/                   # supplied PDF fixture location
  docs/architecture.md
  docs/DEMO_SCRIPT.md
  docs/INTERVIEW_NOTES.md
  requirements.txt
  .env.example
```

## AI tools used

The application uses Groq for structured fact extraction and ambiguous relationship classification. This repository was created with AI-assisted engineering; deterministic validation, grounding, normalization, and tests are included so model output is not blindly trusted.



## Git commands

```powershell
git init
git add .
git commit -m "Build evidence-grounded fact knowledge layer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/superjoin-fact-knowledge-layer.git
git push -u origin main
```

