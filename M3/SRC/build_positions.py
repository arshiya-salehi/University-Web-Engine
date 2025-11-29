"""
Build Word Positions Index
Extra Credit Feature #3
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from position_tracker import PositionTracker


class PositionsBuilder:
    """Builds word positions index"""
    
    def __init__(self, index_dir='index'):
        """Initialize builder"""
        self.index_dir = index_dir
        self.position_tracker = PositionTracker(index_dir)
        
        # Load doc_mapping
        doc_map_file = os.path.join(index_dir, 'doc_mapping.json')
        if not os.path.exists(doc_map_file):
            raise FileNotFoundError(f"Core index not found. Run build_core_index.py first: {doc_map_file}")
        
        with open(doc_map_file, 'r', encoding='utf-8') as f:
            doc_map_data = json.load(f)
        
        if 'url_to_id' in doc_map_data:
            self.url_to_id = doc_map_data['url_to_id']
        else:
            self.url_to_id = {url: int(doc_id) for doc_id, url in doc_map_data.items()}
        
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
            
            # Parse and tokenize with positions
            parsed = self.html_parser.parse(content)
            normal_text = parsed['normal_text']
            important_text = parsed['important_text']
            
            # Tokenize (keeping positions)
            normal_tokens = self.tokenizer.tokenize(normal_text)
            important_tokens = self.tokenizer.tokenize(important_text)
            
            # Stem tokens
            normal_tokens_stemmed = self.stemmer.stem_tokens(normal_tokens)
            important_tokens_stemmed = self.stemmer.stem_tokens(important_tokens)
            
            return url, normal_tokens_stemmed, important_tokens_stemmed
        
        except Exception as e:
            return None
    
    def build_positions(self, data_dir):
        """Build word positions index"""
        print("=" * 70)
        print("EXTRA CREDIT #3: WORD POSITIONS INDEX")
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
                url, normal_tokens, important_tokens = result
                doc_id = self.url_to_id[url]
                self.position_tracker.add_document(doc_id, normal_tokens, important_tokens)
                processed += 1
            else:
                skipped += 1
            
            if i % 1000 == 0:
                print(f"Processed {i}/{total_files} files... (Indexed: {processed}, Skipped: {skipped})")
        
        print(f"\n✓ Processed {processed} documents ({skipped} skipped)\n")
        
        # Save position index
        print("Saving word positions index...")
        self.position_tracker.save_positions()
        
        # Print statistics
        stats = self.position_tracker.get_position_statistics()
        
        print("\n" + "=" * 70)
        print("✓ WORD POSITIONS INDEX COMPLETE!")
        print("=" * 70)
        print(f"\nStatistics:")
        # PositionTracker.get_position_statistics() returns these keys:
        # 'total_unique_terms', 'total_documents_with_positions', 'total_term_positions', 'avg_positions_per_term'
        print(f"  - Total unique terms indexed: {stats.get('total_unique_terms', 0)}")
        print(f"  - Total term positions: {stats.get('total_term_positions', 0)}")
        print(f"  - Documents with positions: {stats.get('total_documents_with_positions', 0)}")
        # PositionTracker stores the filename in `position_file`
        print(f"  - Position index file: {self.position_tracker.position_file}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_positions.py <data_directory> [index_directory]")
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
    
    builder = PositionsBuilder(index_dir)
    builder.build_positions(data_dir)


if __name__ == '__main__':
    main()
