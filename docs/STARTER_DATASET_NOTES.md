# Starter dataset inspection notes

The supplied archive contains two independent domains:

- `delhivery/`: prospectus (2022), FY24 annual-report excerpt, and Q4 FY24 earnings presentation.
- `india-macroeconomy/`: Economic Survey 2024-25, RBI Annual Report 2024-25, and IMF India Article IV 2025 excerpts.

The documents include prose claims, tables, dates, people and organization references, money in INR/USD and scaled values, percentages, operational measurements, and historical versus current periods. They are suitable only as demonstration fixtures; production code has no document, company, term, page, or filename rule.

## Useful demonstration directions

After processing the supplied PDFs with Groq, use Evidence to verify exact page/quote pairs before presenting them. Suitable patterns to look for include:

1. **Corroboration:** Delhivery FY24 figures or operational claims repeated in the annual report and Q4 earnings presentation, possibly with different scaled notation.
2. **Likely contradiction:** a claim that uses the same subject, metric, time, and scope but reports incompatible values. Present it only when both evidence quotes actually meet those conditions; the app does not label historical values as conflicts simply because they differ.
3. **Contextualized difference:** the prospectus has financial and operational series for FY2019-FY2021 and nine-month periods, while later reports cover FY24. Different dates or periods should appear as ⚠️ CONTEXTUALIZED.
4. **Failure/review:** dense multi-column financial tables in the prospectus may lose header-to-value alignment in plain text. The extractor prompt explicitly asks Groq to skip or flag ambiguous rows. Show the original evidence and the review note rather than asserting a result.

This page deliberately does not fabricate exact cross-document facts. The approved demo process is to select the concrete evidence generated from the current run in the UI.
