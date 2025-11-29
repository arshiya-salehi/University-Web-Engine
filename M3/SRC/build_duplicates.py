"""
Build Duplicate Detection Index
Extra Credit Feature #1
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from duplicate_detector import DuplicateDetector


class DuplicateBuilder:
    """Builds duplicate detection index"""
    
    def __init__(self, index_dir='index'):
        """Initialize builder"""
        self.index_dir = index_dir
        self.duplicate_detector = DuplicateDetector(index_dir)
        
        # Load doc_mapping
        doc_map_file = os.path.join(index_dir, 'doc_mapping.json')
        if not os.path.exists(doc_map_file):
            raise FileNotFoundError(f"Core index not found. Run build_core_index.py first: {doc_map_file}")
        
        with open(doc_map_file, 'r', encoding='utf-8') as f:
            doc_map_data = json.load(f)
        
        if 'url_to_id' in doc_map_data:
            self.url_to_id = doc_map_data['url_to_id']
            self.id_to_url = doc_map_data.get('id_to_url', {})
        else:
            self.url_to_id = {url: int(doc_id) for doc_id, url in doc_map_data.items()}
            self.id_to_url = doc_map_data
        
        # Processing components
        self.html_parser = HTMLParser()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
    
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
            if url not in self.url_to_id:
                return None
            
            # Parse and tokenize
            parsed = self.html_parser.parse(content)
            normal_tokens = self.tokenizer.tokenize(parsed['normal_text'])
            normal_tokens = self.stemmer.stem_tokens(normal_tokens)
            
            return url, content, normal_tokens
        
        except Exception as e:
            return None
    
    def build_duplicates(self, data_dir):
        """Build duplicate detection index"""
        print("=" * 70)
        print("EXTRA CREDIT #1: DUPLICATE DETECTION")
        print("=" * 70)
        
        # Find all JSON files
        json_files = list(Path(data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"\nFound {total_files} JSON files to process\n")
        
        # Process each file
        processed = 0
        skipped = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, content, tokens = result
                doc_id = self.url_to_id[url]
                self.duplicate_detector.add_document(doc_id, content, tokens)
                processed += 1
            else:
                skipped += 1
            
            if i % 1000 == 0:
                print(f"Processed {i}/{total_files} files... (Indexed: {processed}, Skipped: {skipped})")
        
        print(f"\n✓ Processed {processed} documents ({skipped} skipped)\n")
        
        # Save duplicate index
        print("Saving duplicate detection index...")
        self.duplicate_detector.save_duplicates(self.id_to_url)
        
        # Print statistics
        exact_dupes = self.duplicate_detector.find_exact_duplicates()
        near_dupes = self.duplicate_detector.find_near_duplicates()
        
        print("\n" + "=" * 70)
        print("✓ DUPLICATE DETECTION INDEX COMPLETE!")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  - Exact duplicate groups: {len(exact_dupes)}")
        print(f"  - Documents with near duplicates: {len(near_dupes)}")
        print(f"  - Index file: {self.duplicate_detector.duplicate_file}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_duplicates.py <data_directory> [index_directory]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    index_dir = sys.argv[2] if len(sys.argv) > 2 else 'index'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(index_dir, 'doc_mapping.json')):
        print(f"Error: Core index not found in {index_dir}")
        print("Run: python build_core_index.py <data_dir> <index_dir> first")
        sys.exit(1)
    
    builder = DuplicateBuilder(index_dir)
    builder.build_duplicates(data_dir)


if __name__ == '__main__':
    main()
