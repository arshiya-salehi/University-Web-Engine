"""
Duplicate Page Detection Module
Detects exact and near-duplicate pages using multiple techniques
Extra Credit: 1-2 points
"""

import hashlib
import json
import os
from collections import defaultdict
from difflib import SequenceMatcher


class DuplicateDetector:
    """Detects exact and near-duplicate pages"""
    
    def __init__(self, index_dir='index'):
        """Initialize duplicate detector"""
        self.index_dir = index_dir
        self.duplicate_file = os.path.join(index_dir, 'duplicates.json')
        self.exact_duplicates = defaultdict(list)  # hash -> [doc_ids]
        self.near_duplicates = defaultdict(list)   # doc_id -> [similar_doc_ids]
        self.doc_hashes = {}  # doc_id -> hash
        self.doc_signatures = {}  # doc_id -> signature (for near-duplicate detection)
        
    def compute_hash(self, content):
        """Compute MD5 hash of content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def compute_signature(self, tokens, window_size=10):
        """
        Compute shingling signature for near-duplicate detection
        Uses shingles (n-grams) of tokens
        """
        if len(tokens) < window_size:
            return set([tuple(tokens)])
        
        shingles = set()
        for i in range(len(tokens) - window_size + 1):
            shingle = tuple(tokens[i:i + window_size])
            shingles.add(shingle)
        
        return frozenset(shingles)
    
    def jaccard_similarity(self, sig1, sig2):
        """Compute Jaccard similarity between two signatures"""
        if not sig1 or not sig2:
            return 0.0
        
        intersection = len(sig1 & sig2)
        union = len(sig1 | sig2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def add_document(self, doc_id, content, tokens):
        """
        Add a document for duplicate detection
        
        Args:
            doc_id: Document ID
            content: Raw document content
            tokens: Tokenized content
        """
        # Exact duplicate detection using hash
        content_hash = self.compute_hash(content)
        self.doc_hashes[doc_id] = content_hash
        self.exact_duplicates[content_hash].append(doc_id)
        
        # Near-duplicate detection using signatures
        signature = self.compute_signature(tokens)
        self.doc_signatures[doc_id] = signature
    
    def find_exact_duplicates(self):
        """Find exact duplicate documents"""
        exact_dupes = {}
        for content_hash, doc_ids in self.exact_duplicates.items():
            if len(doc_ids) > 1:
                exact_dupes[content_hash] = doc_ids
        
        return exact_dupes
    
    def find_near_duplicates(self, similarity_threshold=0.8):
        """
        Find near-duplicate documents using Jaccard similarity
        
        Args:
            similarity_threshold: Minimum similarity (0-1) to be considered near-duplicates
            
        Returns:
            Dict mapping doc_id to list of similar doc_ids
        """
        near_dupes = defaultdict(list)
        doc_ids = list(self.doc_signatures.keys())
        
        for i, doc1 in enumerate(doc_ids):
            for doc2 in doc_ids[i+1:]:
                similarity = self.jaccard_similarity(
                    self.doc_signatures[doc1],
                    self.doc_signatures[doc2]
                )
                
                if similarity >= similarity_threshold:
                    near_dupes[doc1].append((doc2, similarity))
                    near_dupes[doc2].append((doc1, similarity))
        
        return near_dupes
    
    def save_duplicates(self, doc_id_to_url):
        """
        Save duplicate information to file
        
        Args:
            doc_id_to_url: Mapping of doc_id to URL
        """
        exact_dupes = self.find_exact_duplicates()
        near_dupes = self.find_near_duplicates(similarity_threshold=0.8)
        
        # Convert to URL-based format for readability
        exact_by_url = {}
        for content_hash, doc_ids in exact_dupes.items():
            urls = [doc_id_to_url.get(doc_id, f"doc_{doc_id}") for doc_id in doc_ids]
            exact_by_url[content_hash] = urls
        
        near_by_url = {}
        for doc_id, similar_list in near_dupes.items():
            url = doc_id_to_url.get(doc_id, f"doc_{doc_id}")
            similar_urls = [
                (doc_id_to_url.get(sim_id, f"doc_{sim_id}"), score)
                for sim_id, score in similar_list
            ]
            if similar_urls:
                near_by_url[url] = similar_urls
        
        duplicates_info = {
            'exact_duplicates': exact_by_url,
            'near_duplicates': near_by_url,
            'statistics': {
                'total_exact_duplicate_groups': len(exact_by_url),
                'total_pages_with_exact_duplicates': sum(
                    len(urls) for urls in exact_by_url.values()
                ),
                'total_pages_with_near_duplicates': len(near_by_url),
                'near_duplicate_threshold': 0.8
            }
        }
        
        with open(self.duplicate_file, 'w', encoding='utf-8') as f:
            json.dump(duplicates_info, f, indent=2, ensure_ascii=False)
        
        print(f"Saved duplicate information to {self.duplicate_file}")
        print(f"  Exact duplicate groups: {len(exact_by_url)}")
        print(f"  Pages with near duplicates: {len(near_by_url)}")
        
        return duplicates_info
    
    def load_duplicates(self):
        """Load duplicate information from file"""
        if not os.path.exists(self.duplicate_file):
            return None
        
        with open(self.duplicate_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_duplicate_boost(self, doc_id, url_to_id):
        """
        Get a penalty for duplicate pages (lower score)
        
        Returns:
            Float between 0.5 and 1.0 (penalty factor)
        """
        # Check if this document is a duplicate
        if doc_id in self.doc_hashes:
            content_hash = self.doc_hashes[doc_id]
            exact_dupes = self.exact_duplicates.get(content_hash, [])
            
            # If there are exact duplicates, penalize this one
            if len(exact_dupes) > 1:
                # Give penalty based on position in duplicates list
                position = exact_dupes.index(doc_id) + 1
                return max(0.5, 1.0 - (0.1 * position))
        
        return 1.0  # No penalty
