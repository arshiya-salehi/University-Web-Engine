"""
N-gram Indexing Module
Implements 2-gram and 3-gram indexing for phrase-based retrieval
Extra Credit: 1 point
"""

import json
import os
from collections import defaultdict


class NGramIndexer:
    """Creates and manages n-gram indices for phrase queries"""
    
    def __init__(self, index_dir='index'):
        """Initialize n-gram indexer"""
        self.index_dir = index_dir
        self.bigram_file = os.path.join(index_dir, 'bigram_index.json')
        self.trigram_file = os.path.join(index_dir, 'trigram_index.json')
        
        # In-memory n-gram indices
        self.bigrams = defaultdict(lambda: defaultdict(lambda: {'tf': 0, 'is_important': False}))
        self.trigrams = defaultdict(lambda: defaultdict(lambda: {'tf': 0, 'is_important': False}))
        
        self.loaded = False
    
    def generate_ngrams(self, tokens, n):
        """
        Generate n-grams from tokens
        
        Args:
            tokens: List of tokens
            n: Size of n-gram (2 for bigrams, 3 for trigrams)
            
        Returns:
            List of n-gram tuples
        """
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    def add_document(self, doc_id, tokens, important_tokens):
        """
        Add n-grams from a document
        
        Args:
            doc_id: Document ID
            tokens: List of normal tokens
            important_tokens: List of important tokens
        """
        # Generate bigrams
        bigrams = self.generate_ngrams(tokens, 2)
        bigrams_important = self.generate_ngrams(important_tokens, 2)
        
        # Generate trigrams
        trigrams = self.generate_ngrams(tokens, 3)
        trigrams_important = self.generate_ngrams(important_tokens, 3)
        
        # Add bigrams to index
        important_bigram_set = set(bigrams_important)
        for bigram in bigrams:
            bigram_str = ' '.join(bigram)
            self.bigrams[bigram_str][doc_id]['tf'] += 1
            if bigram in important_bigram_set:
                self.bigrams[bigram_str][doc_id]['is_important'] = True
        
        # Add trigrams to index
        important_trigram_set = set(trigrams_important)
        for trigram in trigrams:
            trigram_str = ' '.join(trigram)
            self.trigrams[trigram_str][doc_id]['tf'] += 1
            if trigram in important_trigram_set:
                self.trigrams[trigram_str][doc_id]['is_important'] = True
    
    def save_indices(self):
        """Save n-gram indices to disk"""
        # Convert to JSON-serializable format
        bigram_data = {}
        for bigram, postings in self.bigrams.items():
            bigram_data[bigram] = {str(doc_id): data for doc_id, data in postings.items()}
        
        trigram_data = {}
        for trigram, postings in self.trigrams.items():
            trigram_data[trigram] = {str(doc_id): data for doc_id, data in postings.items()}
        
        # Save bigrams
        with open(self.bigram_file, 'w', encoding='utf-8') as f:
            json.dump(bigram_data, f, indent=2)
        
        # Save trigrams
        with open(self.trigram_file, 'w', encoding='utf-8') as f:
            json.dump(trigram_data, f, indent=2)
        
        print(f"Saved {len(bigram_data)} bigrams to {self.bigram_file}")
        print(f"Saved {len(trigram_data)} trigrams to {self.trigram_file}")
    
    def load_indices(self):
        """Load n-gram indices from disk"""
        if os.path.exists(self.bigram_file):
            with open(self.bigram_file, 'r', encoding='utf-8') as f:
                bigram_data = json.load(f)
                for bigram, postings in bigram_data.items():
                    for doc_id_str, data in postings.items():
                        self.bigrams[bigram][int(doc_id_str)] = data
        
        if os.path.exists(self.trigram_file):
            with open(self.trigram_file, 'r', encoding='utf-8') as f:
                trigram_data = json.load(f)
                for trigram, postings in trigram_data.items():
                    for doc_id_str, data in postings.items():
                        self.trigrams[trigram][int(doc_id_str)] = data
        
        self.loaded = True
    
    def search_bigrams(self, bigram_query):
        """
        Search for bigram
        
        Args:
            bigram_query: String like "machine learning"
            
        Returns:
            Dict of doc_id -> posting data
        """
        if not self.loaded:
            self.load_indices()
        
        return dict(self.bigrams.get(bigram_query.lower(), {}))
    
    def search_trigrams(self, trigram_query):
        """
        Search for trigram
        
        Args:
            trigram_query: String like "machine learning algorithms"
            
        Returns:
            Dict of doc_id -> posting data
        """
        if not self.loaded:
            self.load_indices()
        
        return dict(self.trigrams.get(trigram_query.lower(), {}))
    
    def get_ngram_statistics(self):
        """Get statistics about n-grams"""
        return {
            'total_bigrams': len(self.bigrams),
            'total_trigrams': len(self.trigrams),
            'total_bigram_postings': sum(len(p) for p in self.bigrams.values()),
            'total_trigram_postings': sum(len(p) for p in self.trigrams.values()),
        }
