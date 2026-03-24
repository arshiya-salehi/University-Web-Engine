# University Web Engine

A full-stack academic web search engine that indexes tens of thousands of UCI ICS web pages and supports fast, ranked retrieval under strict memory and latency constraints.

---

## Features

- **Custom** inverted index for the full developer ICS corpus (∼56K pages, 88 subdomains) with on-disk storage and controlled memory usage.  
- Term processing pipeline with:
  - HTML cleaning and broken-HTML handling  
  - Alphanumeric tokenization (no stopword removal)  
  - Porter-style stemming for both documents and queries.  
- Weighted term representation that boosts:
  - Title terms  
  - Heading tags (h1–h3)  
  - Bold/strong text.  
- Boolean AND query support plus ranked retrieval using tf-idf, extended with additional heuristics for Milestone 3.  

---

## Architecture

### Indexer

- Parses JSON files for each crawled page:
  - `url`: canonical URL of the page  
  - `content`: raw HTML content  
  - `encoding`: best-effort encoding info.  
- Builds an inverted index where each posting stores:
  - Document id / URL  
  - Term frequency and derived tf-idf weight  
  - Optional extra attributes (e.g., structural importance, positions).  
- Implements external-memory construction:
  - Accumulates postings in memory  
  - Flushes to partial index files on disk at least three times  
  - Merges partial indexes into a final on-disk index, optionally split by term ranges.  

### Search Component

- Console-based interactive interface that:
  - Prompts for free-text queries  
  - Tokenizes and stems query terms  
  - Reads only the necessary postings from on-disk index files (does not load full index into RAM).  
- Scoring model:
  - Baseline tf-idf ranking  
  - Structural weighting for titles/headings/bold text  
  - Hooks for additional signals (e.g., link-based or positional signals).  
- Designed to answer queries over the full developer corpus with target latency ≤300 ms per query on typical hardware.  

---

## Project Context

This project implements the **Algorithms** and Data Structures Developer flavor of the UCI search engine assignment for CS/SE students, focusing on:

- Efficient data structures and file layouts for large-scale indexing  
- Low-memory operation (index size > memory size)  
- Fast query evaluation with ranked results  
- Robust handling of noisy, real-world HTML.  

The system satisfies the three milestones:

- **Milestone 1 – Index Construction:** Build inverted index, report document and token statistics, and total on-disk index size.  
- **Milestone 2 – Retrieval:** Implement Boolean AND retrieval and top-5 ranked URLs for specified test queries (e.g., “cristina lopes”, “machine learning”).  
- **Milestone 3 – Search Engine:** Optimize ranking and runtime using at least 20 evaluation queries, improving poor cases while preserving good ones and maintaining low memory footprint.  

---

## Getting Started

### Prerequisites

- Python 3.x (recommended) with common libraries for:
  - HTML parsing (e.g., BeautifulSoup-like parser)  
  - Stemming (e.g., Porter stemmer via NLTK or similar)  
  - JSON and file I/O utilities.  
- Download the **developer** dataset (`developer.zip`) from the UCI course resources and extract it so that the indexer can read the domain folders.  

### Usage

1. **Build the index**

   ```bash
   python indexer.py --data-path /path/to/developer \
                     --index-out /path/to/index_dir

- Streams through all JSON files.  
- Flushes partial indexes to disk multiple times.  
- Merges into final on-disk index structure.  

---

## Run the search engine

```bash
python search.py --index-path /path/to/index_dir
Prompts for queries in a loop.

Outputs ranked URLs for each query with scores.

Evaluation
Functional evaluation with at least 20 queries, including:

Provided baseline queries for the course.

Additional self-designed queries that initially performed poorly and were used to guide improvements.

Performance evaluation emphasizes:

Query latency (goal ≤300 ms).

Memory footprint below total index size during both indexing and search.

This project showcases systems-level IR engineering: building a search engine from scratch (indexer + query engine) for tens of thousands of web pages without relying on external indexing libraries like Lucene or ElasticSearch.
