"""
Link Analysis Module
Implements HITS and PageRank algorithms for link-based ranking
Extra Credit: 1.5-2.5 points
"""

import json
import os
import math
from collections import defaultdict


class LinkAnalyzer:
    """Implements HITS and PageRank algorithms"""
    
    def __init__(self, index_dir='index'):
        """Initialize link analyzer"""
        self.index_dir = index_dir
        self.pagerank_file = os.path.join(index_dir, 'pagerank.json')
        self.hits_file = os.path.join(index_dir, 'hits.json')
        
        # Graph structure: doc_id -> set of outgoing links
        self.outlinks = defaultdict(set)
        self.inlinks = defaultdict(set)
        
        # Scores
        self.pagerank_scores = {}
        self.hits_hubs = {}
        self.hits_authorities = {}
        
        self.loaded = False
    
    def add_link(self, source_doc_id, target_doc_id):
        """
        Add a link from source to target document
        
        Args:
            source_doc_id: Source document ID
            target_doc_id: Target document ID
        """
        if source_doc_id != target_doc_id:  # Ignore self-loops
            self.outlinks[source_doc_id].add(target_doc_id)
            self.inlinks[target_doc_id].add(source_doc_id)
    
    def compute_pagerank(self, num_docs=None, damping_factor=0.85, iterations=20, tolerance=0.001):
        """
        Compute PageRank scores for all documents
        
        Args:
            num_docs: Total number of documents
            damping_factor: Damping factor (typically 0.85)
            iterations: Number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dict of doc_id -> pagerank score
        """
        print("Computing PageRank...")

        # If num_docs is not provided, try to infer from core doc_mapping
        if num_docs is None:
            doc_map_file = os.path.join(self.index_dir, 'doc_mapping.json')
            try:
                if os.path.exists(doc_map_file):
                    with open(doc_map_file, 'r', encoding='utf-8') as f:
                        mapping = json.load(f)
                    if isinstance(mapping, dict):
                        if 'url_to_id' in mapping:
                            ids = [int(v) for v in mapping['url_to_id'].values()]
                        else:
                            ids = [int(k) for k in mapping.keys()]
                        num_docs = max(ids) + 1 if ids else 0
                else:
                    num_docs = 0
            except Exception:
                num_docs = 0

        # Fallback: derive from observed graph if still unknown
        if not num_docs:
            all_ids = set(self.outlinks.keys()) | set(self.inlinks.keys())
            for targets in self.outlinks.values():
                all_ids.update(targets)
            for sources in self.inlinks.values():
                all_ids.update(sources)
            num_docs = max(all_ids) + 1 if all_ids else 0

        if num_docs == 0:
            print("  No documents available for PageRank computation.")
            self.pagerank_scores = {}
            return {}

        # Initialize scores
        initial_score = 1.0 / num_docs
        scores = {doc_id: initial_score for doc_id in range(num_docs)}
        
        for iteration in range(iterations):
            new_scores = {}
            
            for doc_id in range(num_docs):
                # Calculate new score
                rank = (1 - damping_factor) / num_docs
                
                # Add contribution from inlinks
                if doc_id in self.inlinks:
                    for source_id in self.inlinks[doc_id]:
                        # Number of outlinks from source
                        num_outlinks = len(self.outlinks[source_id])
                        if num_outlinks > 0:
                            rank += damping_factor * (scores[source_id] / num_outlinks)
                
                new_scores[doc_id] = rank
            
            # Check convergence
            diff = sum(abs(new_scores[i] - scores[i]) for i in range(num_docs))
            scores = new_scores
            
            if (iteration + 1) % 5 == 0:
                print(f"  Iteration {iteration + 1}: difference = {diff:.6f}")
            
            if diff < tolerance:
                print(f"  Converged after {iteration + 1} iterations")
                break
        
        self.pagerank_scores = scores
        return scores
    
    def compute_hits(self, query_related_docs=None, iterations=10, tolerance=0.001):
        """
        Compute HITS (Hubs and Authorities) scores for documents
        
        Args:
            query_related_docs: Set of document IDs relevant to query
            iterations: Number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Tuple of (hubs_dict, authorities_dict)
        """
        print("Computing HITS...")

        # If no specific set provided, compute HITS over all known nodes in the graph
        if query_related_docs is None:
            all_ids = set(self.outlinks.keys()) | set(self.inlinks.keys())
            for targets in self.outlinks.values():
                all_ids.update(targets)
            for sources in self.inlinks.values():
                all_ids.update(sources)
            query_related_docs = set(all_ids)

        if not query_related_docs:
            return {}, {}
        
        # Initialize scores
        hub_scores = {doc_id: 1.0 for doc_id in query_related_docs}
        auth_scores = {doc_id: 1.0 for doc_id in query_related_docs}
        
        for iteration in range(iterations):
            # Update authority scores
            new_auth_scores = {}
            for doc_id in query_related_docs:
                score = 0.0
                if doc_id in self.inlinks:
                    for source_id in self.inlinks[doc_id]:
                        if source_id in hub_scores:
                            score += hub_scores[source_id]
                new_auth_scores[doc_id] = score
            
            # Update hub scores
            new_hub_scores = {}
            for doc_id in query_related_docs:
                score = 0.0
                if doc_id in self.outlinks:
                    for target_id in self.outlinks[doc_id]:
                        if target_id in auth_scores:
                            score += auth_scores[target_id]
                new_hub_scores[doc_id] = score
            
            # Normalize
            auth_sum = sum(new_auth_scores.values())
            hub_sum = sum(new_hub_scores.values())
            
            if auth_sum > 0:
                new_auth_scores = {doc_id: score / auth_sum for doc_id, score in new_auth_scores.items()}
            if hub_sum > 0:
                new_hub_scores = {doc_id: score / hub_sum for doc_id, score in new_hub_scores.items()}
            
            # Check convergence
            auth_diff = sum(abs(new_auth_scores.get(i, 0) - auth_scores.get(i, 0)) for i in query_related_docs)
            hub_diff = sum(abs(new_hub_scores.get(i, 0) - hub_scores.get(i, 0)) for i in query_related_docs)
            
            auth_scores = new_auth_scores
            hub_scores = new_hub_scores
            
            if (iteration + 1) % 5 == 0:
                print(f"  Iteration {iteration + 1}: auth_diff = {auth_diff:.6f}, hub_diff = {hub_diff:.6f}")
            
            if auth_diff < tolerance and hub_diff < tolerance:
                print(f"  Converged after {iteration + 1} iterations")
                break
        
        self.hits_hubs = hub_scores
        self.hits_authorities = auth_scores
        
        return hub_scores, auth_scores
    
    def get_pagerank(self, doc_id):
        """Get PageRank score for a document"""
        return self.pagerank_scores.get(doc_id, 0.0)
    
    def get_hits_hub(self, doc_id):
        """Get HITS hub score for a document"""
        return self.hits_hubs.get(doc_id, 0.0)
    
    def get_hits_authority(self, doc_id):
        """Get HITS authority score for a document"""
        return self.hits_authorities.get(doc_id, 0.0)
    
    def save_scores(self):
        """Save PageRank and HITS scores to disk"""
        # Save PageRank
        with open(self.pagerank_file, 'w', encoding='utf-8') as f:
            json.dump(self.pagerank_scores, f, indent=2)
        
        # Save HITS
        hits_data = {
            'hubs': self.hits_hubs,
            'authorities': self.hits_authorities
        }
        with open(self.hits_file, 'w', encoding='utf-8') as f:
            json.dump(hits_data, f, indent=2)
        
        print(f"Saved PageRank scores to {self.pagerank_file}")
        print(f"Saved HITS scores to {self.hits_file}")

    # Backwards-compatible aliases expected by builders
    def save_links(self):
        """Compatibility wrapper: save PageRank and HITS scores"""
        return self.save_scores()

    def load_links(self):
        """Compatibility wrapper: load PageRank and HITS scores"""
        return self.load_scores()
    
    def load_scores(self):
        """Load PageRank and HITS scores from disk"""
        if os.path.exists(self.pagerank_file):
            with open(self.pagerank_file, 'r', encoding='utf-8') as f:
                self.pagerank_scores = json.load(f)
        
        if os.path.exists(self.hits_file):
            with open(self.hits_file, 'r', encoding='utf-8') as f:
                hits_data = json.load(f)
                self.hits_hubs = hits_data.get('hubs', {})
                self.hits_authorities = hits_data.get('authorities', {})
        
        self.loaded = True
    
    def get_graph_statistics(self):
        """Get statistics about the link graph"""
        total_links = sum(len(outlinks) for outlinks in self.outlinks.values())
        docs_with_outlinks = len([d for d in self.outlinks.values() if len(d) > 0])
        docs_with_inlinks = len(self.inlinks)
        
        return {
            'total_links': total_links,
            'documents_with_outlinks': docs_with_outlinks,
            'documents_with_inlinks': docs_with_inlinks,
            'avg_outlinks': total_links / docs_with_outlinks if docs_with_outlinks > 0 else 0,
            'avg_inlinks': total_links / docs_with_inlinks if docs_with_inlinks > 0 else 0,
        }

    def get_link_statistics(self):
        """Return statistics in the format expected by builders"""
        graph_stats = self.get_graph_statistics()
        return {
            'total_links': graph_stats.get('total_links', 0),
            'docs_with_outgoing_links': graph_stats.get('documents_with_outlinks', 0),
            'docs_with_incoming_links': graph_stats.get('documents_with_inlinks', 0),
            'pagerank_nodes': len(self.pagerank_scores) if self.pagerank_scores else 0,
            'hubs_nodes': len(self.hits_hubs) if self.hits_hubs else 0,
            'authorities_nodes': len(self.hits_authorities) if self.hits_authorities else 0,
        }
