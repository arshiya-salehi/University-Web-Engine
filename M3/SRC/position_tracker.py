"""
Word Position Tracking Module
Tracks word positions in documents for phrase queries and position-based ranking
Extra Credit: 2 points
"""

import json
import os
from collections import defaultdict


class PositionTracker:
    """Tracks word positions in documents for advanced retrieval"""
    
    def __init__(self, index_dir='index'):
        """Initialize position tracker"""
        self.index_dir = index_dir
        self.position_file = os.path.join(index_dir, 'word_positions.json')
        
        # Structure: {term: {doc_id: [positions]}}
        self.positions = defaultdict(lambda: defaultdict(list))
        self.loaded = False
    
    def add_token_positions(self, doc_id, tokens):
        """
        Add token positions for a document
        
        Args:
            doc_id: Document ID
            tokens: List of tokens in order
        """
        for position, token in enumerate(tokens):
            self.positions[token][doc_id].append(position)

    def add_document(self, doc_id, normal_tokens, important_tokens=None):
        """
        Add positions for a full document. This method is the expected
        interface used by the builders. It records positions for
        `normal_tokens` and (optionally) `important_tokens`. Important
        tokens are appended after normal tokens so positions remain
        comparable within the document.

        Args:
            doc_id: Document ID (int)
            normal_tokens: list of tokens from normal text
            important_tokens: list of tokens from important text (optional)
        """
        if normal_tokens:
            for pos, token in enumerate(normal_tokens):
                self.positions[token][doc_id].append(pos)

        if important_tokens:
            offset = len(normal_tokens) if normal_tokens else 0
            for pos, token in enumerate(important_tokens, start=offset):
                self.positions[token][doc_id].append(pos)
    
    def get_positions(self, term, doc_id):
        """
        Get positions of a term in a document
        
        Args:
            term: The term to look up
            doc_id: Document ID
            
        Returns:
            List of positions (0-indexed)
        """
        return self.positions[term].get(doc_id, [])
    
    def find_phrase(self, terms, doc_id):
        """
        Find if a phrase exists in a document at any position
        
        Args:
            terms: List of terms forming a phrase
            doc_id: Document ID
            
        Returns:
            List of starting positions where phrase appears, or empty list
        """
        if not terms or not doc_id in self.positions.get(terms[0], {}):
            return []
        
        # Get positions of first term
        first_term_positions = self.positions[terms[0]][doc_id]
        phrase_positions = []
        
        # For each occurrence of first term, check if phrase continues
        for start_pos in first_term_positions:
            phrase_found = True
            
            for i, term in enumerate(terms[1:], 1):
                expected_pos = start_pos + i
                
                if term not in self.positions:
                    phrase_found = False
                    break
                
                if doc_id not in self.positions[term]:
                    phrase_found = False
                    break
                
                if expected_pos not in self.positions[term][doc_id]:
                    phrase_found = False
                    break
            
            if phrase_found:
                phrase_positions.append(start_pos)
        
        return phrase_positions
    
    def save_positions(self):
        """Save position information to disk"""
        # Convert to JSON-serializable format
        position_data = {}
        for term, doc_positions in self.positions.items():
            position_data[term] = {str(doc_id): positions for doc_id, positions in doc_positions.items()}
        
        with open(self.position_file, 'w', encoding='utf-8') as f:
            json.dump(position_data, f, indent=2)
        
        total_positions = sum(sum(len(pos) for pos in doc_pos.values()) for doc_pos in self.positions.values())
        print(f"Saved position information to {self.position_file}")
        print(f"  Unique terms with positions: {len(position_data)}")
        print(f"  Total term positions: {total_positions}")
    
    def load_positions(self):
        """Load position information from disk"""
        if not os.path.exists(self.position_file):
            return
        
        with open(self.position_file, 'r', encoding='utf-8') as f:
            position_data = json.load(f)
            for term, doc_positions in position_data.items():
                for doc_id_str, positions in doc_positions.items():
                    self.positions[term][int(doc_id_str)] = positions
        
        self.loaded = True
    
    def get_proximity_score(self, terms, doc_id, max_distance=50):
        """
        Calculate proximity score for terms in a document
        Closer terms get higher scores
        
        Args:
            terms: List of query terms
            doc_id: Document ID
            max_distance: Maximum allowed distance between terms
            
        Returns:
            Float between 0 and 1
        """
        if len(terms) < 2:
            return 1.0
        
        # Get positions for each term
        all_positions = []
        for term in terms:
            if term in self.positions and doc_id in self.positions[term]:
                all_positions.append(self.positions[term][doc_id])
            else:
                return 0.0  # Term not found
        
        # Find minimum distance between term positions
        min_distance = max_distance
        
        for pos1 in all_positions[0]:
            for pos2 in all_positions[1]:
                distance = abs(pos1 - pos2)
                if distance < min_distance:
                    min_distance = distance
        
        # Convert distance to proximity score (closer = higher)
        if min_distance > max_distance:
            return 0.0
        
        return 1.0 - (min_distance / max_distance)
    
    def get_position_statistics(self):
        """Get statistics about term positions"""
        total_terms = len(self.positions)
        total_docs_with_positions = sum(len(doc_pos) for doc_pos in self.positions.values())
        total_positions = sum(sum(len(pos) for pos in doc_pos.values()) for doc_pos in self.positions.values())
        
        return {
            'total_unique_terms': total_terms,
            'total_documents_with_positions': total_docs_with_positions,
            'total_term_positions': total_positions,
            'avg_positions_per_term': total_positions / total_terms if total_terms > 0 else 0,
        }
