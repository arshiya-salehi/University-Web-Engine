"""
Build extra-credit auxiliary indices from existing core index and dataset.
Processes dataset again to extract duplicate, n-gram, position, anchor, and link data.
Does NOT rebuild the inverted index or doc_mapping (those are already created).
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from duplicate_detector import DuplicateDetector
from ngram_indexer import NGramIndexer
from position_tracker import PositionTracker
from anchor_text_indexer import AnchorTextIndexer
from link_analyzer import LinkAnalyzer


class ExtraCreditIndexBuilder:
    """Build extra-credit indices using existing core index"""
    
    def __init__(self, data_dir, index_dir='index', output_dir=None):
        """Initialize builder with existing core index"""
        if output_dir is None:
            output_dir = index_dir
        
        self.data_dir = data_dir
        self.index_dir = index_dir
        self.output_dir = output_dir
        
        # Load existing doc_mapping
        doc_map_file = os.path.join(index_dir, 'doc_mapping.json')
        with open(doc_map_file, 'r') as f:
            doc_map_data = json.load(f)
        
        # Extract the actual mappings (may be nested under 'url_to_id' and 'id_to_url')
        if isinstance(doc_map_data, dict):
            if 'url_to_id' in doc_map_data:
                self.url_to_doc_id = doc_map_data['url_to_id']
                self.doc_mapping = doc_map_data.get('id_to_url', {})
            else:
                # Old format: doc_id -> URL directly
                self.url_to_doc_id = {url: int(doc_id) for doc_id, url in doc_map_data.items()}
                self.doc_mapping = {str(v): k for k, v in self.url_to_doc_id.items()}
        else:
            raise ValueError("Unexpected doc_mapping format")
        
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
        
        # Track links
        self.links_to_process = []
    
    def process_json_file(self, file_path):
        """Process a single JSON file"""
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
            
            # Skip if not in doc_mapping
            if url not in self.url_to_doc_id:
                return None
            
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
        """Add document to extra-credit indices"""
        doc_id = self.url_to_doc_id[url]
        
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
            
            # Resolve and sanitize target URL
            try:
                target_url = urljoin(url, href)
            except Exception:
                continue
            
            if '#' in target_url:
                target_url = target_url.split('#')[0]
            
            # Anchor text
            try:
                self.anchor_indexer.add_anchor_text(url, target_url, anchor_text)
            except Exception:
                continue
            
            # Store for link graph
            self.links_to_process.append((url, target_url))
    
    def build_indices(self):
        """Build all extra-credit indices"""
        print(f"Building extra-credit indices from {self.data_dir}...")
        print("="*70)
        print(f"Using existing core index with {len(self.doc_mapping)} documents\n")
        
        # Find all JSON files
        json_files = list(Path(self.data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"Found {total_files} JSON files to process\n")
        
        # Process each file
        processed = 0
        skipped = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, normal_tokens, important_tokens, links, content = result
                self.add_document(url, normal_tokens, important_tokens, links, content)
                processed += 1
            else:
                skipped += 1
            
            if i % 100 == 0:
                print(f"Processed {i}/{total_files} files... (Indexed: {processed}, Skipped: {skipped})")
        
        print(f"\n✓ Processed {processed} documents ({skipped} skipped)\n")
        
        # Save extra credit indices
        print("Saving extra credit features...")
        self._save_extra_credit_features()
        
        # Build link graph and compute link-based scores
        print("\nBuilding link graph for HITS/PageRank...")
        self._build_link_graph()
        
        print("\n" + "="*70)
        print("✓ Extra-credit index building complete!")
        print("="*70)
        
        self._print_statistics()
    
    def _save_extra_credit_features(self):
        """Save all extra credit features"""
        try:
            # Duplicates
            print("  • Saving duplicate detection...")
            self.duplicate_detector.save_duplicates(self.doc_mapping)
            
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
                num_docs=len(self.doc_mapping),
                iterations=20
            )
            self.link_analyzer.save_scores()
            print(f"    - PageRank computed for {len(pagerank)} documents")
        except Exception as e:
            print(f"    ✗ PageRank error: {e}")
        
        # Compute HITS
        print("  • Computing HITS...")
        try:
            all_docs = set(range(len(self.doc_mapping)))
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
        print("\nEXTRA-CREDIT STATISTICS:")
        print("-"*70)
        
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


def build_extra_credit_indices(data_dir, index_dir='index'):
    """Main function"""
    builder = ExtraCreditIndexBuilder(data_dir, index_dir)
    builder.build_indices()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python build_extra_credit_indices.py <data_directory> [index_directory]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    index_dir = sys.argv[2] if len(sys.argv) > 2 else 'index'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(index_dir, 'doc_mapping.json')):
        print(f"Error: Core index not found: {index_dir}/doc_mapping.json")
        sys.exit(1)
    
    build_extra_credit_indices(data_dir, index_dir)
