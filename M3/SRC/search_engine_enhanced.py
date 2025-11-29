"""
M3 Enhanced Search Engine with Extra Credit Features
Integrates all extra credit implementations:
- Duplicate detection
- HITS/PageRank
- N-gram indexing
- Word positions
- Anchor text indexing
"""

import json
import os
import sys
import math
import re
from collections import defaultdict

from stemmer import Stemmer
from tokenizer import Tokenizer

# Import all extra credit modules
from duplicate_detector import DuplicateDetector
from link_analyzer import LinkAnalyzer
from ngram_indexer import NGramIndexer
from position_tracker import PositionTracker
from anchor_text_indexer import AnchorTextIndexer


class M3EnhancedSearchEngine:
    """Enhanced search engine with all extra credit features"""
    
    def __init__(self, index_dir='index'):
        """Initialize enhanced search engine"""
        self.index_dir = index_dir
        self.index_file = os.path.join(index_dir, 'inverted_index.json')
        self.doc_mapping_file = os.path.join(index_dir, 'doc_mapping.json')
        
        # Initialize components
        self.stemmer = Stemmer()
        self.tokenizer = Tokenizer()
        
        # Document mappings
        self.doc_mappings = None
        self.total_docs = 0
        
        # Caches
        self.df_cache = {}
        self.postings_cache = {}
        self.cache_max_size = 500
        
        # Extra credit modules
        self.duplicate_detector = DuplicateDetector(index_dir)
        self.link_analyzer = LinkAnalyzer(index_dir)
        self.ngram_indexer = NGramIndexer(index_dir)
        self.position_tracker = PositionTracker(index_dir)
        self.anchor_indexer = AnchorTextIndexer(index_dir)
        
        # Flags for available features
        self.has_duplicates = False
        self.has_pagerank = False
        self.has_hits = False
        self.has_ngrams = False
        self.has_positions = False
        self.has_anchors = False
        
        # Load everything
        self._load_doc_mappings()
        self._load_extra_credit_features()
    
    def _load_doc_mappings(self):
        """Load document mappings"""
        if not os.path.exists(self.doc_mapping_file):
            raise FileNotFoundError(f"Document mapping file not found: {self.doc_mapping_file}")
        
        with open(self.doc_mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.doc_mappings = {
                'url_to_id': data.get('url_to_id', {}),
                'id_to_url': {int(k): v for k, v in data.get('id_to_url', {}).items()}
            }
        
        self.total_docs = len(self.doc_mappings['url_to_id'])
        print(f"Loaded {self.total_docs} document mappings")
    
    def _load_extra_credit_features(self):
        """Load all extra credit features"""
        print("Loading extra credit features...")
        
        # Load duplicates
        try:
            self.duplicate_detector.load_duplicates()
            self.has_duplicates = os.path.exists(self.duplicate_detector.duplicate_file)
            if self.has_duplicates:
                print("  ✓ Duplicate detection loaded")
        except Exception as e:
            print(f"  ✗ Could not load duplicates: {e}")
        
        # Load PageRank and HITS
        try:
            self.link_analyzer.load_scores()
            self.has_pagerank = len(self.link_analyzer.pagerank_scores) > 0
            self.has_hits = len(self.link_analyzer.hits_authorities) > 0
            if self.has_pagerank:
                print("  ✓ PageRank loaded")
            if self.has_hits:
                print("  ✓ HITS loaded")
        except Exception as e:
            print(f"  ✗ Could not load link analysis: {e}")
        
        # Load n-grams
        try:
            self.ngram_indexer.load_indices()
            self.has_ngrams = len(self.ngram_indexer.bigrams) > 0
            if self.has_ngrams:
                print("  ✓ N-gram indexing loaded")
        except Exception as e:
            print(f"  ✗ Could not load n-grams: {e}")
        
        # Load positions
        try:
            self.position_tracker.load_positions()
            self.has_positions = len(self.position_tracker.positions) > 0
            if self.has_positions:
                print("  ✓ Word positions loaded")
        except Exception as e:
            print(f"  ✗ Could not load positions: {e}")
        
        # Load anchor text
        try:
            self.anchor_indexer.load_anchor_index()
            self.has_anchors = len(self.anchor_indexer.anchor_text) > 0
            if self.has_anchors:
                print("  ✓ Anchor text indexing loaded")
        except Exception as e:
            print(f"  ✗ Could not load anchor text: {e}")
        
        print("Extra credit features loaded\n")
    
    def _extract_term_from_json(self, term, file_content):
        """Extract specific term from JSON"""
        pattern = rf'"{re.escape(term)}"\s*:\s*(\{{[^}}]*(?:\{{[^}}]*\}}[^}}]*)*\}})'
        match = re.search(pattern, file_content)
        
        if not match:
            return None
        
        try:
            term_json_str = match.group(1)
            term_data = json.loads('{' + f'"{term}": {term_json_str}' + '}')
            return term_data.get(term, {})
        except:
            return None
    
    def _get_postings(self, term):
        """Get postings for a term with caching"""
        if term in self.postings_cache:
            return self.postings_cache[term]
        
        if not os.path.exists(self.index_file):
            return {}
        # For reliability, load the JSON index and access the term directly.
        # The file is expected to be reasonably sized; loading into memory
        # simplifies correct extraction and avoids brittle regex parsing.
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        except Exception:
            return {}

        term_data = index_data.get(term)
        if not term_data:
            return {}

        postings = {int(doc_id): posting for doc_id, posting in term_data.items()}
        
        # Add to cache (with LRU eviction)
        if len(self.postings_cache) >= self.cache_max_size:
            self.postings_cache.pop(next(iter(self.postings_cache)))
        
        self.postings_cache[term] = postings
        return postings
    
    def search(self, query, use_extra_credit=True):
        """
        Search with all extra credit features
        
        Args:
            query: Search query string
            use_extra_credit: Whether to use extra credit features in ranking
            
        Returns:
            List of (doc_id, url, score) tuples, sorted by score
        """
        # Tokenize and stem query
        tokens = self.tokenizer.tokenize(query)
        stemmed_tokens = self.stemmer.stem_tokens(tokens)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tokens = []
        for token in stemmed_tokens:
            if token not in seen:
                unique_tokens.append(token)
                seen.add(token)
        
        if not unique_tokens:
            return []
        
        # Get postings for each term
        all_postings = []
        for token in unique_tokens:
            postings = self._get_postings(token)
            if postings:
                all_postings.append(postings)
        
        if not all_postings:
            return []
        
        # Find documents containing all terms (AND query)
        # Start with smallest posting list
        all_postings.sort(key=len)
        result_docs = set(all_postings[0].keys())
        
        for postings in all_postings[1:]:
            result_docs &= set(postings.keys())
        
        if not result_docs:
            return []
        
        # Calculate scores
        scores = {}
        for doc_id in result_docs:
            score = self._calculate_score(
                doc_id,
                unique_tokens,
                all_postings,
                use_extra_credit=use_extra_credit
            )
            scores[doc_id] = score
        
        # Sort by score
        results = [
            (doc_id, self.doc_mappings['id_to_url'].get(doc_id, ''), score)
            for doc_id, score in scores.items()
        ]
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results
    
    def _calculate_score(self, doc_id, terms, postings_list, use_extra_credit=True):
        """Calculate ranking score with all features"""
        # Base TF-IDF score
        score = 0.0
        
        for i, term in enumerate(terms):
            postings = postings_list[i]
            
            if doc_id not in postings:
                continue
            
            posting_data = postings[doc_id]
            tf = posting_data.get('tf', 1)
            is_important = posting_data.get('is_important', False)
            
            # Sublinear TF
            tf_score = math.log(1 + tf)
            
            # Smoothed IDF
            df = len(postings)
            idf_score = math.log((self.total_docs + 1) / (df + 1)) + 1
            
            # Term score with importance boost
            term_score = tf_score * idf_score
            if is_important:
                term_score *= 2.0
            
            score += term_score
        
        # Query normalization
        score /= math.sqrt(len(terms))
        
        # Complete match bonus
        if len(terms) > 1:
            score *= 1.15
        
        # Extra credit features
        if use_extra_credit:
            # Duplicate penalty
            if self.has_duplicates:
                dup_boost = self.duplicate_detector.get_duplicate_boost(
                    doc_id,
                    self.doc_mappings['url_to_id']
                )
                score *= dup_boost
            
            # PageRank boost
            if self.has_pagerank:
                pagerank = self.link_analyzer.get_pagerank(doc_id)
                score += pagerank * 0.1  # 10% weight
            
            # HITS authority boost
            if self.has_hits:
                authority = self.link_analyzer.get_hits_authority(doc_id)
                score += authority * 0.05  # 5% weight
            
            # Proximity score (if we have positions)
            if self.has_positions and len(terms) > 1:
                proximity = self.position_tracker.get_proximity_score(terms, doc_id)
                score += proximity * 0.1  # 10% weight
        
        return score
    
    def get_feature_stats(self):
        """Get statistics about available features"""
        stats = {
            'duplicate_detection': self.has_duplicates,
            'pagerank': self.has_pagerank,
            'hits': self.has_hits,
            'ngram_indexing': self.has_ngrams,
            'word_positions': self.has_positions,
            'anchor_text': self.has_anchors,
        }
        
        if self.has_duplicates:
            dup_info = self.duplicate_detector.load_duplicates()
            if dup_info:
                stats['duplicate_stats'] = dup_info.get('statistics', {})
        
        if self.has_pagerank:
            stats['num_pagerank_docs'] = len(self.link_analyzer.pagerank_scores)
        
        if self.has_hits:
            stats['num_hits_docs'] = len(self.link_analyzer.hits_authorities)
        
        if self.has_ngrams:
            stats['ngram_stats'] = self.ngram_indexer.get_ngram_statistics()
        
        if self.has_positions:
            stats['position_stats'] = self.position_tracker.get_position_statistics()
        
        if self.has_anchors:
            stats['anchor_stats'] = self.anchor_indexer.get_anchor_statistics()
        
        return stats
