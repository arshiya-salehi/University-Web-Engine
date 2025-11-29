# How To Run — M3 Web Search Engine (Summary)

Quick start (recommended)
1. Ensure `M3/index/` contains the core index files (`inverted_index.json`, `doc_mapping.json`). If not, build the core index.
2. From `M3/SRC` run:

```bash
# Build everything (may take ~30-100 minutes depending on hardware)
python3 build_all.py ../Data ../index

# Verify indices
python3 verify_features.py ../index

# Run web UI
python3 web_search_m3.py
# then open http://127.0.0.1:5001
```

Build individual features
- Core index: `python3 build_core_index.py ../Data ../index`
- Duplicates: `python3 build_duplicates.py ../Data ../index`
- N-grams: `python3 build_ngrams.py ../Data ../index`
- Positions: `python3 build_positions.py ../Data ../index`
- Anchors: `python3 build_anchors.py ../Data ../index`
- Links: `python3 build_links.py ../Data ../index`

Testing & verification
- Run `python3 test_queries_m3.py` or `python3 test_all_features.py` to run the test harness (30 queries + extra-credit tests).
- `/features` endpoint: `curl http://127.0.0.1:5001/features` returns which extras are loaded.
- `/search` endpoint accepts POST requests with JSON payload and returns ranked results.

Notes & tips
- Use small test runs first (a subset of `M3/Data`) while debugging.
- If a builder skips many files, normalize URLs between `Data/*.json` and `doc_mapping.json` to reduce skips (anchor and link builders are sensitive to URL mismatches).
- For reproducibility, consider creating a `requirements.txt` and a virtual environment.

Save as `HOW_TO_RUN_SUMMARY.md`.
