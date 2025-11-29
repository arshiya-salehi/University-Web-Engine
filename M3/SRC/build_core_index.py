"""
Build Core Index Only
Builds the basic inverted index and document mappings
(No extra-credit features)
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from disk_indexer import DiskBasedIndexer


class CoreIndexBuilder:
    """Builds core inverted index without extra-credit features"""
    
    def __init__(self, output_dir='index', max_docs_in_memory=10000):
        """Initialize builder"""
        self.output_dir = output_dir
        self.max_docs_in_memory = max_docs_in_memory
        
        # Core indexing
        self.disk_indexer = DiskBasedIndexer(output_dir, max_docs_in_memory)
        
        # Processing components
        self.html_parser = HTMLParser()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
        
        # Track URLs
        self.url_to_doc_id = {}
    
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
            
            # Parse HTML
            parsed = self.html_parser.parse(content)
            
            # Tokenize
            normal_tokens = self.tokenizer.tokenize(parsed['normal_text'])
            important_tokens = self.tokenizer.tokenize(parsed['important_text'])
            
            # Stem tokens
            normal_tokens = self.stemmer.stem_tokens(normal_tokens)
            important_tokens = self.stemmer.stem_tokens(important_tokens)
            
            return url, normal_tokens, important_tokens
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            return None
    
    def add_document(self, url, normal_tokens, important_tokens):
        """Add document to index"""
        # Get or create doc_id
        if url not in self.url_to_doc_id:
            doc_id = len(self.url_to_doc_id)
            self.url_to_doc_id[url] = doc_id
        
        # Add to disk indexer (basic indexing)
        self.disk_indexer.add_document(url, normal_tokens, important_tokens)
    
    def build_index(self, data_dir):
        """Build core index"""
        print("=" * 70)
        print("CORE INDEX BUILDER")
        print("Building basic inverted index (no extra-credit features)")
        print("=" * 70)
        
        # Find all JSON files
        json_files = list(Path(data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"\nFound {total_files} JSON files to process\n")
        
        # Process each file
        processed = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, normal_tokens, important_tokens = result
                self.add_document(url, normal_tokens, important_tokens)
                processed += 1
            
            if i % 1000 == 0:
                print(f"Processed {i}/{total_files} files... (Documents: {len(self.url_to_doc_id)})")
        
        print(f"\n✓ Processed {processed} documents\n")
        
        # Finalize basic indexing
        print("Finalizing index...")
        self.disk_indexer.finalize()
        
        print("\n" + "=" * 70)
        print("✓ CORE INDEX BUILDING COMPLETE!")
        print("=" * 70)
        
        # Print statistics
        print(f"\nStatistics:")
        print(f"  - Total documents: {len(self.url_to_doc_id)}")
        print(f"  - Total unique terms: {len(self.disk_indexer.index)}")
        print(f"  - Index location: {self.output_dir}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_core_index.py <data_directory> [output_directory]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'index'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    builder = CoreIndexBuilder(output_dir)
    builder.build_index(data_dir)


if __name__ == '__main__':
    main()
