"""
Anchor Text Indexing Module
Extracts and indexes anchor text from links pointing to target pages
Extra Credit: 1 point
"""

import json
import os
import re
from collections import defaultdict
from urllib.parse import urljoin, urlparse


class AnchorTextIndexer:
    """Extracts and indexes anchor text for target pages"""
    
    def __init__(self, index_dir='index'):
        """Initialize anchor text indexer"""
        self.index_dir = index_dir
        self.anchor_file = os.path.join(index_dir, 'anchor_text_index.json')
        
        # Structure: {target_url: {source_url: [anchor_texts]}}
        self.anchor_text = defaultdict(lambda: defaultdict(list))
        
        # Also track by doc_id: {doc_id: {source_url: [anchor_texts]}}
        self.anchor_by_docid = defaultdict(lambda: defaultdict(list))
        
        self.loaded = False
    
    def extract_anchors_from_html(self, html_content, source_url, base_domain=None):
        """
        Extract anchor text and links from HTML content
        
        Args:
            html_content: HTML content as string
            source_url: URL of the source page
            base_domain: Base domain to filter links (e.g., 'ics.uci.edu')
            
        Returns:
            List of (target_url, anchor_text) tuples
        """
        anchors = []
        
        # Simple regex-based anchor extraction (can be improved with BeautifulSoup)
        # Pattern: <a href="...">...</a>
        anchor_pattern = r'<a\s+href=["\']?([^\s>"\']+)["\']?[^>]*>([^<]+)</a>'
        
        matches = re.finditer(anchor_pattern, html_content, re.IGNORECASE)
        
        for match in matches:
            href = match.group(1).strip()
            anchor_text = match.group(2).strip()
            
            if not anchor_text:  # Skip empty anchor text
                continue
            
            # Resolve relative URLs
            target_url = urljoin(source_url, href)
            
            # Remove fragment
            if '#' in target_url:
                target_url = target_url.split('#')[0]
            
            # Filter by domain if specified
            if base_domain:
                target_domain = urlparse(target_url).netloc
                if base_domain not in target_domain:
                    continue
            
            anchors.append((target_url, anchor_text))
        
        return anchors
    
    def extract_anchors_from_soup(self, soup, source_url, base_domain=None):
        """
        Extract anchors using BeautifulSoup (more reliable)
        
        Args:
            soup: BeautifulSoup object
            source_url: URL of the source page
            base_domain: Base domain to filter links
            
        Returns:
            List of (target_url, anchor_text) tuples
        """
        try:
            from bs4 import BeautifulSoup
            has_bs4 = True
        except ImportError:
            has_bs4 = False
            return []
        
        anchors = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            anchor_text = link.get_text().strip()
            
            if not anchor_text or not href:
                continue
            
            # Resolve relative URLs
            target_url = urljoin(source_url, href)
            
            # Remove fragment
            if '#' in target_url:
                target_url = target_url.split('#')[0]
            
            # Filter by domain if specified
            if base_domain:
                target_domain = urlparse(target_url).netloc
                if base_domain not in target_domain:
                    continue
            
            anchors.append((target_url, anchor_text))
        
        return anchors
    
    def add_anchor_text(self, source_url, target_url, anchor_text):
        """
        Add anchor text from source to target
        
        Args:
            source_url: URL of page containing the link
            target_url: URL being linked to
            anchor_text: Text of the link
        """
        self.anchor_text[target_url][source_url].append(anchor_text)
    
    def add_anchor_text_for_doc(self, doc_id, source_url, target_url, anchor_text):
        """
        Add anchor text using document IDs
        
        Args:
            doc_id: Target document ID
            source_url: URL of source page
            target_url: URL being linked to
            anchor_text: Text of the link
        """
        self.anchor_by_docid[doc_id][source_url].append(anchor_text)
    
    def get_anchor_text(self, target_url):
        """
        Get all anchor text pointing to a URL
        
        Args:
            target_url: URL to get anchors for
            
        Returns:
            Dict of source_url -> list of anchor texts
        """
        return dict(self.anchor_text.get(target_url, {}))
    
    def get_anchor_text_for_doc(self, doc_id):
        """
        Get all anchor text pointing to a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dict of source_url -> list of anchor texts
        """
        return dict(self.anchor_by_docid.get(doc_id, {}))
    
    def get_combined_anchor_text(self, target_url):
        """
        Get all anchor text pointing to a URL as a single string
        
        Args:
            target_url: URL to get anchors for
            
        Returns:
            String of all anchor texts combined
        """
        anchors = self.anchor_text.get(target_url, {})
        all_text = []
        
        for source_url, texts in anchors.items():
            all_text.extend(texts)
        
        return ' '.join(all_text)
    
    def save_anchor_index(self):
        """Save anchor text index to disk"""
        # Convert to JSON-serializable format
        anchor_data = {}
        for target_url, sources in self.anchor_text.items():
            anchor_data[target_url] = {source_url: texts for source_url, texts in sources.items()}
        
        with open(self.anchor_file, 'w', encoding='utf-8') as f:
            json.dump(anchor_data, f, indent=2, ensure_ascii=False)
        
        total_links = sum(sum(len(texts) for texts in sources.values()) for sources in self.anchor_text.values())
        print(f"Saved anchor text index to {self.anchor_file}")
        print(f"  Pages with incoming links: {len(anchor_data)}")
        print(f"  Total anchor links: {total_links}")
    
    def load_anchor_index(self):
        """Load anchor text index from disk"""
        if not os.path.exists(self.anchor_file):
            return
        
        with open(self.anchor_file, 'r', encoding='utf-8') as f:
            anchor_data = json.load(f)
            for target_url, sources in anchor_data.items():
                for source_url, texts in sources.items():
                    self.anchor_text[target_url][source_url] = texts
        
        self.loaded = True
    
    def get_anchor_statistics(self):
        """Get statistics about anchor text"""
        pages_with_anchors = len(self.anchor_text)
        total_anchor_links = sum(
            sum(len(texts) for texts in sources.values())
            for sources in self.anchor_text.values()
        )
        
        return {
            'pages_with_incoming_links': pages_with_anchors,
            'total_anchor_links': total_anchor_links,
            'avg_links_per_page': total_anchor_links / pages_with_anchors if pages_with_anchors > 0 else 0,
        }

    # Backwards-compatible aliases expected by builders
    def save_anchors(self):
        """Alias for save_anchor_index for backward compatibility"""
        return self.save_anchor_index()

    def load_anchors(self):
        """Alias for load_anchor_index for backward compatibility"""
        return self.load_anchor_index()
