# Reports Summary — M3 Web Search Engine

This aggregates the reporting and test outputs described across the docs.

Deliverables produced by the project
- `m3_test_results.json` — JSON with test-query run timings and per-query results.
- `milestone3_report_developer.pdf` — Generated PDF report with results and method explanations.
- `M3_SUBMISSION_REPORT.txt`, `FEATURE_SUMMARY.txt` — Plain-text submission summaries.
- `index_stats.json` — Index statistics (number of terms, partial indexes, sizes).

How to regenerate reports
1. Run tests:
   `python3 test_queries_m3.py` (or `python3 test_all_features.py`)
2. Generate PDF:
   `python3 generate_m3_report.py` or `python3 generate_reports.py`

Key metrics to highlight in reports
- Total documents indexed (from `doc_mapping.json`).
- Core index size (bytes, human-readable).
- Which extra-credit indices were populated: duplicates, ngrams, positions, anchors (may be stub), pagerank/hits.
- Test query average latency and distribution (good/poor/challenging categories).
- Number of partial index offloads during core build (should be >= 3 for developer option).

Notes
- Anchor text and HITS coverage may be low due to URL normalization mismatches between `Data` JSON `url` fields and `doc_mapping.json` keys. Document this in the final report and show the attempted fixes.

Save as `REPORTS_SUMMARY.md`.
