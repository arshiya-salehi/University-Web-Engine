"""
Enhanced Index Builder with Extra Credit Features
Builds index with:
- Duplicate detection
- N-gram indexing  
- Word position tracking
- Anchor text indexing
- Link analysis (HITS/PageRank)
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from disk_indexer import DiskBasedIndexer
from duplicate_detector import DuplicateDetector
from ngram_indexer import NGramIndexer
from position_tracker import PositionTracker
from anchor_text_indexer import AnchorTextIndexer
from link_analyzer import LinkAnalyzer


class EnhancedIndexBuilder:
    """Builds index with all extra credit features"""
    
    def __init__(self, output_dir='index', max_docs_in_memory=10000):
        """Initialize builder"""
        self.output_dir = output_dir
        self.max_docs_in_memory = max_docs_in_memory
        
        # Core indexing
        self.disk_indexer = DiskBasedIndexer(output_dir, max_docs_in_memory)
        
        # Extra credit modules
        self.duplicate_detector = DuplicateDetector(output_dir)
        self.ngram_indexer = NGramIndexer(output_dir)
        self.position_tracker = PositionTracker(output_dir)
        self.anchor_indexer = AnchorTextIndexer(output_dir)
        self.link_analyzer = LinkAnalyzer(output_dir)
        
        # Processing components
        self.html_parser = HTMLParser()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
        
        # Track URLs for link analysis
        self.url_to_doc_id = {}
        self.doc_id_count = 0
        
        # Track link targets for later document ID mapping
        self.links_to_process = []
    
    def process_json_file(self, file_path):
        """
        Process a single JSON file
        
        Returns:
            (url, tokens, important_tokens, links) or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            url = data.get('url', '')
            content = data.get('content', '')
            
            if not url or not content:
                return None
            
            # Remove fragment
            if '#' in url:
                url = url.split('#')[0]
            
            # Parse HTML
            parsed = self.html_parser.parse(content)
            
            # Get links
            links = parsed.get('links', [])
            
            # Tokenize
            normal_tokens = self.tokenizer.tokenize(parsed['normal_text'])
            important_tokens = self.tokenizer.tokenize(parsed['important_text'])
            
            # Stem tokens
            normal_tokens = self.stemmer.stem_tokens(normal_tokens)
            important_tokens = self.stemmer.stem_tokens(important_tokens)
            
            return url, normal_tokens, important_tokens, links, content
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            return None
    
    def add_document(self, url, normal_tokens, important_tokens, links, raw_content):
        """Add document with all extra credit features"""
        # Get or create doc_id
        if url not in self.url_to_doc_id:
            doc_id = len(self.url_to_doc_id)
            self.url_to_doc_id[url] = doc_id
        else:
            doc_id = self.url_to_doc_id[url]
        
        # Add to disk indexer (basic indexing)
        self.disk_indexer.add_document(url, normal_tokens, important_tokens)
        
        # Duplicate detection
        self.duplicate_detector.add_document(doc_id, raw_content, normal_tokens)
        
        # N-gram indexing
        self.ngram_indexer.add_document(doc_id, normal_tokens, important_tokens)
        
        # Position tracking
        self.position_tracker.add_token_positions(doc_id, normal_tokens)
        
        # Process links for anchor text and link graph
        for href, anchor_text in links:
            # Skip empty hrefs and non-http(s) schemes
            if not href or not isinstance(href, str):
                continue
            lower = href.lower()
            if lower.startswith('javascript:') or lower.startswith('mailto:'):
                continue

            # Resolve and sanitize target URL; guard against malformed hosts
            try:
                target_url = urljoin(url, href)
            except Exception:
                # Skip malformed href that breaks url parsing
                continue

            if '#' in target_url:
                target_url = target_url.split('#')[0]

            # Anchor text
            try:
                self.anchor_indexer.add_anchor_text(url, target_url, anchor_text)
            except Exception:
                # Anchor indexing shouldn't break the whole build
                continue

            # Store for link graph processing
            self.links_to_process.append((url, target_url))
    
    def build_index(self, data_dir):
        """Build complete index with all features"""
        print(f"Building enhanced index from {data_dir}...")
        print("="*70)
        
        # Find all JSON files
        json_files = list(Path(data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"Found {total_files} JSON files to process\n")
        
        # Process each file
        processed = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, normal_tokens, important_tokens, links, content = result
                self.add_document(url, normal_tokens, important_tokens, links, content)
                processed += 1
            
            if i % 100 == 0:
                print(f"Processed {i}/{total_files} files... "
                      f"(Documents: {len(self.url_to_doc_id)})")
        
        print(f"\n✓ Processed {processed} documents\n")
        
        # Finalize basic indexing
        print("Finalizing basic indexing...")
        self.disk_indexer.finalize()
        
        # Save extra credit indices
        print("\nSaving extra credit features...")
        self._save_extra_credit_features()
        
        # Build link graph and compute link-based scores
        print("\nBuilding link graph for HITS/PageRank...")
        self._build_link_graph()
        
        print("\n" + "="*70)
        print("✓ Index building complete!")
        print("="*70)
        
        self._print_statistics()
    
    def _save_extra_credit_features(self):
        """Save all extra credit features"""
        try:
            # Duplicates
            print("  • Saving duplicate detection...")
            self.duplicate_detector.save_duplicates(self.disk_indexer.doc_id_to_url)
            
            # N-grams
            print("  • Saving n-gram indices...")
            self.ngram_indexer.save_indices()
            
            # Positions
            print("  • Saving word positions...")
            self.position_tracker.save_positions()
            
            # Anchor text
            print("  • Saving anchor text index...")
            self.anchor_indexer.save_anchor_index()
            
        except Exception as e:
            print(f"  ✗ Error saving features: {e}")
    
    def _build_link_graph(self):
        """Build link graph and compute HITS/PageRank"""
        print("  • Building link graph...")
        
        # Convert links to doc_ids
        processed_links = 0
        for source_url, target_url in self.links_to_process:
            source_id = self.url_to_doc_id.get(source_url)
            target_id = self.url_to_doc_id.get(target_url)
            
            if source_id is not None and target_id is not None:
                self.link_analyzer.add_link(source_id, target_id)
                processed_links += 1
        
        print(f"    - {processed_links} links added to graph")
        
        # Compute PageRank
        print("  • Computing PageRank...")
        try:
            pagerank = self.link_analyzer.compute_pagerank(
                num_docs=len(self.url_to_doc_id),
                iterations=20
            )
            self.link_analyzer.save_scores()
            print(f"    - PageRank computed for {len(pagerank)} documents")
        except Exception as e:
            print(f"    ✗ PageRank error: {e}")
        
        # Compute HITS
        print("  • Computing HITS...")
        try:
            # Use all documents as query-related (full graph HITS)
            all_docs = set(self.url_to_doc_id.values())
            if len(all_docs) > 1:
                hubs, authorities = self.link_analyzer.compute_hits(
                    all_docs,
                    iterations=10
                )
                print(f"    - HITS computed ({len(hubs)} hubs, {len(authorities)} authorities)")
        except Exception as e:
            print(f"    ✗ HITS error: {e}")
    
    def _print_statistics(self):
        """Print comprehensive statistics"""
        print("\nFINAL STATISTICS:")
        print("-"*70)
        
        # Basic stats
        print(f"\n• Basic Indexing:")
        print(f"  - Total documents: {len(self.url_to_doc_id)}")
        print(f"  - Total unique terms: {len(self.disk_indexer.index)}")
        
        # Duplicate stats
        exact_dupes = self.duplicate_detector.find_exact_duplicates()
        near_dupes = self.duplicate_detector.find_near_duplicates()
        print(f"\n• Duplicate Detection:")
        print(f"  - Exact duplicate groups: {len(exact_dupes)}")
        print(f"  - Documents with near duplicates: {len(near_dupes)}")
        
        # N-gram stats
        ngram_stats = self.ngram_indexer.get_ngram_statistics()
        print(f"\n• N-gram Indexing:")
        print(f"  - Bigrams: {ngram_stats['total_bigrams']}")
        print(f"  - Trigrams: {ngram_stats['total_trigrams']}")
        
        # Position stats
        pos_stats = self.position_tracker.get_position_statistics()
        print(f"\n• Word Positions:")
        print(f"  - Terms with positions: {pos_stats['total_unique_terms']}")
        print(f"  - Documents with positions: {pos_stats['total_documents_with_positions']}")
        
        # Anchor stats
        anchor_stats = self.anchor_indexer.get_anchor_statistics()
        print(f"\n• Anchor Text:")
        print(f"  - Pages with incoming links: {anchor_stats['pages_with_incoming_links']}")
        print(f"  - Total anchor links: {anchor_stats['total_anchor_links']}")
        
        # Link graph stats
        link_stats = self.link_analyzer.get_graph_statistics()
        print(f"\n• Link Analysis:")
        print(f"  - Total links: {link_stats['total_links']}")
        print(f"  - Documents with outlinks: {link_stats['documents_with_outlinks']}")
        print(f"  - Documents with inlinks: {link_stats['documents_with_inlinks']}")


def build_enhanced_index(data_dir, output_dir='index'):
    """Main function to build enhanced index"""
    builder = EnhancedIndexBuilder(output_dir)
    builder.build_index(data_dir)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python build_enhanced_index.py <data_directory> [output_directory]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'index'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    build_enhanced_index(data_dir, output_dir)
