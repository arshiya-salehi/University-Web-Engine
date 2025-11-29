"""
Build Anchor Text Index
Extra Credit Feature #4
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from tokenizer import Tokenizer
from stemmer import Stemmer
from anchor_text_indexer import AnchorTextIndexer


class AnchorBuilder:
    """Builds anchor text index"""
    
    def __init__(self, index_dir='index'):
        """Initialize builder"""
        self.index_dir = index_dir
        self.anchor_indexer = AnchorTextIndexer(index_dir)
        
        # Load doc_mapping
        doc_map_file = os.path.join(index_dir, 'doc_mapping.json')
        if not os.path.exists(doc_map_file):
            raise FileNotFoundError(f"Core index not found. Run build_core_index.py first: {doc_map_file}")
        
        with open(doc_map_file, 'r', encoding='utf-8') as f:
            doc_map_data = json.load(f)
        
        if 'url_to_id' in doc_map_data:
            self.url_to_id = doc_map_data['url_to_id']
            self.id_to_url = {v: k for k, v in doc_map_data['url_to_id'].items()}
        else:
            self.url_to_id = {url: int(doc_id) for doc_id, url in doc_map_data.items()}
            self.id_to_url = {int(doc_id): url for doc_id, url in doc_map_data.items()}
        
        # Processing components
        self.html_parser = HTMLParser()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
    
    def normalize_url(self, href, source_url):
        """Resolve and normalize an href relative to the source URL.

        This uses urljoin to handle relative links and strips URL fragments.
        """
        try:
            from urllib.parse import urljoin
            target = urljoin(source_url, href)
        except Exception:
            target = href

        if '#' in target:
            target = target.split('#')[0]

        return target
    
    def process_json_file(self, file_path):
        """Process a single JSON file and extract anchors"""
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
            
            # Parse to extract anchors
            parsed = self.html_parser.parse(content)
            anchors = parsed.get('anchors', [])
            
            return url, anchors
        
        except Exception as e:
            return None
    
    def build_anchors(self, data_dir):
        """Build anchor text index"""
        print("=" * 70)
        print("EXTRA CREDIT #4: ANCHOR TEXT INDEXING")
        print("=" * 70)
        
        # Find all JSON files
        json_files = list(Path(data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"\nFound {total_files} JSON files to process\n")
        
        # Process each file
        processed = 0
        skipped = 0
        total_anchors = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, anchors = result
                doc_id = self.url_to_id[url]
                
                # Process anchors
                for anchor_data in anchors:
                    href = anchor_data.get('href', '')
                    text = anchor_data.get('text', '')

                    if not href or not text:
                        continue

                    # Resolve relative hrefs against the source page URL
                    target = self.normalize_url(href, url)

                    # Tokenize and stem anchor text for possible indexing (not required by anchor_indexer)
                    tokens = self.tokenizer.tokenize(text)
                    tokens = self.stemmer.stem_tokens(tokens)

                    # If target maps to a doc_id, store by doc_id; otherwise store by URL
                    if target in self.url_to_id:
                        target_doc_id = int(self.url_to_id[target])
                        self.anchor_indexer.add_anchor_text_for_doc(target_doc_id, url, target, text)
                    else:
                        self.anchor_indexer.add_anchor_text(url, target, text)

                    total_anchors += 1
                
                processed += 1
            else:
                skipped += 1
            
            if i % 1000 == 0:
                print(f"Processed {i}/{total_files} files... (Indexed: {processed}, Skipped: {skipped}, Anchors: {total_anchors})")
        
        print(f"\n✓ Processed {processed} documents ({skipped} skipped, {total_anchors} anchors)\n")
        
        # Save anchor index
        print("Saving anchor text index...")
        # Use the anchor_indexer's canonical save method
        self.anchor_indexer.save_anchor_index()

        # Print statistics
        stats = self.anchor_indexer.get_anchor_statistics()
        
        print("\n" + "=" * 70)
        print("✓ ANCHOR TEXT INDEX COMPLETE!")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  - Pages with incoming links: {stats.get('pages_with_incoming_links', 0)}")
        print(f"  - Total anchor links: {stats.get('total_anchor_links', 0)}")
        print(f"  - Avg links per page: {stats.get('avg_links_per_page', 0):.2f}")
        print(f"  - Anchor index file: {self.anchor_indexer.anchor_file}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_anchors.py <data_directory> [index_directory]")
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
    
    builder = AnchorBuilder(index_dir)
    builder.build_anchors(data_dir)


if __name__ == '__main__':
    main()
