"""
Build Link Analysis Index (PageRank and HITS)
Extra Credit Feature #5
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from html_parser import HTMLParser
from link_analyzer import LinkAnalyzer


class LinksBuilder:
    """Builds link analysis indices (PageRank and HITS)"""
    
    def __init__(self, index_dir='index'):
        """Initialize builder"""
        self.index_dir = index_dir
        self.link_analyzer = LinkAnalyzer(index_dir)
        
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
    
    def normalize_url(self, url):
        """Normalize URL for comparison"""
        if url.startswith('/'):
            url = 'http://example.com' + url
        if '#' in url:
            url = url.split('#')[0]
        return url
    
    def process_json_file(self, file_path):
        """Process a single JSON file and extract links"""
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
            
            # Parse to extract links
            parsed = self.html_parser.parse(content)
            anchors = parsed.get('anchors', [])
            
            links = []
            for anchor_data in anchors:
                href = anchor_data.get('href', '')
                if href:
                    href = self.normalize_url(href)
                    links.append(href)
            
            return url, links
        
        except Exception as e:
            return None
    
    def build_links(self, data_dir):
        """Build link graph and compute PageRank/HITS"""
        print("=" * 70)
        print("EXTRA CREDIT #5: LINK ANALYSIS (PageRank & HITS)")
        print("=" * 70)
        
        # Find all JSON files
        json_files = list(Path(data_dir).rglob('*.json'))
        total_files = len(json_files)
        
        print(f"\nFound {total_files} JSON files to process\n")
        print("Step 1: Building link graph...")
        
        # Process each file and build link graph
        processed = 0
        skipped = 0
        total_links = 0
        for i, json_file in enumerate(json_files, 1):
            result = self.process_json_file(json_file)
            if result:
                url, links = result
                doc_id = self.url_to_id[url]
                
                # Add links to graph
                for target_url in links:
                    target_id = self.url_to_id.get(target_url)
                    if target_id is not None:
                        self.link_analyzer.add_link(doc_id, target_id)
                        total_links += 1
                
                processed += 1
            else:
                skipped += 1
            
            if i % 1000 == 0:
                print(f"Processed {i}/{total_files} files... (Indexed: {processed}, Skipped: {skipped}, Links: {total_links})")
        
        print(f"\n✓ Built link graph: {processed} documents, {total_links} links ({skipped} skipped)\n")
        
        # Compute PageRank
        print("Step 2: Computing PageRank...")
        self.link_analyzer.compute_pagerank(damping_factor=0.85, iterations=30, tolerance=1e-6)
        
        # Compute HITS
        print("Step 3: Computing HITS...")
        self.link_analyzer.compute_hits(iterations=30, tolerance=1e-6)
        
        # Save indices
        print("\nStep 4: Saving indices...")
        self.link_analyzer.save_links()
        
        # Print statistics
        stats = self.link_analyzer.get_link_statistics()
        
        print("\n" + "=" * 70)
        print("✓ LINK ANALYSIS COMPLETE!")
        print("=" * 70)
        print(f"\nLink Graph Statistics:")
        print(f"  - Total links: {stats['total_links']}")
        print(f"  - Documents with outgoing links: {stats['docs_with_outgoing_links']}")
        print(f"  - Documents with incoming links: {stats['docs_with_incoming_links']}")
        
        print(f"\nPageRank Statistics:")
        print(f"  - Nodes with PageRank: {stats['pagerank_nodes']}")
        print(f"  - PageRank file: {self.link_analyzer.pagerank_file}")
        
        print(f"\nHITS Statistics:")
        print(f"  - Hubs: {stats['hubs_nodes']}")
        print(f"  - Authorities: {stats['authorities_nodes']}")
        print(f"  - HITS file: {self.link_analyzer.hits_file}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_links.py <data_directory> [index_directory]")
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
    
    builder = LinksBuilder(index_dir)
    builder.build_links(data_dir)


if __name__ == '__main__':
    main()
