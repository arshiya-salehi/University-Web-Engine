# Requirements Summary — M3 Web Search Engine

Runtime & System
- Python: 3.8+ recommended (3.6+ supported in docs). Use system or conda Python. Virtualenv previously included but removed from submission; use `python3 -m venv venv` and `pip install -r requirements.txt` to recreate environment.

Primary Python dependencies (inferred from docs and code)
- `flask` — web UI
- `nltk` — tokenization / optional language tools
- `beautifulsoup4`, `lxml` — HTML parsing
- `reportlab` — PDF report generation
- `requests` — testing scripts and web checks

Data
- Raw corpus: `M3/Data/` (many JSON files; ~55k files).
- Index output: `M3/index/` (inverted index, doc mapping, extras).

Disk / Memory
- Index files expected to be large (hundreds of MB combined). Keep disk space available and do not rely on loading entire index into memory.
- Builders may offload partial indices multiple times (>= 3 offloads expected for compliance with developer option constraints).

Developer tools (optional)
- `jq` (helpful for JSON debugging)
- `tar` / `gzip` (for backups)

Save this file as `REQUIREMENTS_SUMMARY.md`.
