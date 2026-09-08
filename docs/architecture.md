# Architecture

```mermaid
flowchart LR
  U[PDF upload] --> P[Page-aware PDF parser]
  P --> C[Page-bounded chunks]
  C --> G[Groq structured fact extraction]
  G --> V[Pydantic validation + evidence check]
  V --> N[Deterministic normalization]
  N --> S[(SQLite)]
  S --> M[Candidate retrieval]
  M --> R[Context-aware relationship reasoner]
  R --> S
  S --> UI[Streamlit inspection UI]
```

The pipeline persists each document, page-bounded chunk, fact, and relationship separately. Later uploads are incremental: only newly extracted facts are compared against existing facts.
