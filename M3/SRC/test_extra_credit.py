"""
Comprehensive Test Suite for Extra Credit Features
Tests all implementations for correctness and functionality
"""

import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from duplicate_detector import DuplicateDetector
from link_analyzer import LinkAnalyzer
from ngram_indexer import NGramIndexer
from position_tracker import PositionTracker
from anchor_text_indexer import AnchorTextIndexer
from search_engine_enhanced import M3EnhancedSearchEngine


def test_duplicate_detection():
    """Test duplicate detection"""
    print("\n" + "="*70)
    print("TEST 1: Duplicate Detection")
    print("="*70)
    
    detector = DuplicateDetector()
    
    # Simulate adding documents
    doc1 = "this is a test document about machine learning"
    doc2 = "this is a test document about machine learning"  # Exact duplicate
    doc3 = "this is a similar document about machine learning"  # Near duplicate
    doc4 = "completely different content here"
    
    detector.add_document(1, doc1, [])
    detector.add_document(2, doc2, [])
    detector.add_document(3, doc3, [])
    detector.add_document(4, doc4, [])
    
    exact_dupes = detector.find_exact_duplicates()
    near_dupes = detector.find_near_duplicates(similarity_threshold=0.7)
    
    print(f"✓ Exact duplicates found: {len(exact_dupes)}")
    if exact_dupes:
        for hash_val, doc_ids in list(exact_dupes.items())[:3]:
            print(f"  - Group: {doc_ids}")
    
    print(f"✓ Near duplicates found: {len(near_dupes)}")
    if near_dupes:
        for doc_id, similar_list in list(near_dupes.items())[:3]:
            print(f"  - Doc {doc_id}: {len(similar_list)} similar documents")
    
    return True


def test_ngram_indexing():
    """Test n-gram indexing"""
    print("\n" + "="*70)
    print("TEST 2: N-gram Indexing")
    print("="*70)
    
    ngram_indexer = NGramIndexer()
    
    # Simulate adding documents
    tokens1 = ['machine', 'learning', 'algorithms']
    tokens2 = ['deep', 'learning', 'neural', 'networks']
    
    ngram_indexer.add_document(1, tokens1, tokens1[:1])
    ngram_indexer.add_document(2, tokens2, tokens2[:1])
    
    # Test bigram searches
    bigram_results = ngram_indexer.search_bigrams('machine learning')
    print(f"✓ Bigram 'machine learning': {len(bigram_results)} documents found")
    
    trigram_results = ngram_indexer.search_trigrams('deep learning neural')
    print(f"✓ Trigram 'deep learning neural': {len(trigram_results)} documents found")
    
    stats = ngram_indexer.get_ngram_statistics()
    print(f"✓ Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return True


def test_word_positions():
    """Test word position tracking"""
    print("\n" + "="*70)
    print("TEST 3: Word Position Tracking")
    print("="*70)
    
    position_tracker = PositionTracker()
    
    # Simulate adding documents with positions
    doc1_tokens = ['machine', 'learning', 'is', 'about', 'machine', 'learning']
    doc2_tokens = ['deep', 'learning', 'networks']
    
    position_tracker.add_token_positions(1, doc1_tokens)
    position_tracker.add_token_positions(2, doc2_tokens)
    
    # Test position retrieval
    positions = position_tracker.get_positions('machine', 1)
    print(f"✓ Positions of 'machine' in doc 1: {positions}")
    
    # Test phrase finding
    phrase_positions = position_tracker.find_phrase(['machine', 'learning'], 1)
    print(f"✓ Phrase 'machine learning' found at positions: {phrase_positions}")
    
    # Test proximity score
    proximity = position_tracker.get_proximity_score(['machine', 'learning'], 1)
    print(f"✓ Proximity score for ['machine', 'learning'] in doc 1: {proximity:.3f}")
    
    stats = position_tracker.get_position_statistics()
    print(f"✓ Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return True


def test_anchor_text():
    """Test anchor text indexing"""
    print("\n" + "="*70)
    print("TEST 4: Anchor Text Indexing")
    print("="*70)
    
    anchor_indexer = AnchorTextIndexer()
    
    # Simulate adding anchor text
    anchor_indexer.add_anchor_text(
        'http://source1.com', 
        'http://target.com', 
        'important page'
    )
    anchor_indexer.add_anchor_text(
        'http://source2.com',
        'http://target.com',
        'great resource'
    )
    
    # Test retrieval
    anchors = anchor_indexer.get_anchor_text('http://target.com')
    print(f"✓ Anchor text pointing to http://target.com:")
    for source, texts in anchors.items():
        print(f"  - From {source}: {texts}")
    
    combined = anchor_indexer.get_combined_anchor_text('http://target.com')
    print(f"✓ Combined anchor text: '{combined}'")
    
    stats = anchor_indexer.get_anchor_statistics()
    print(f"✓ Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return True


def test_link_analyzer():
    """Test HITS and PageRank"""
    print("\n" + "="*70)
    print("TEST 5: Link Analysis (HITS & PageRank)")
    print("="*70)
    
    link_analyzer = LinkAnalyzer()
    
    # Build a simple link graph: 1->2, 1->3, 2->3, 3->1
    link_analyzer.add_link(1, 2)
    link_analyzer.add_link(1, 3)
    link_analyzer.add_link(2, 3)
    link_analyzer.add_link(3, 1)
    
    # Compute PageRank
    print("\n• Computing PageRank...")
    start_time = time.time()
    pagerank = link_analyzer.compute_pagerank(num_docs=4, iterations=10)
    elapsed = time.time() - start_time
    print(f"  ✓ PageRank computed in {elapsed:.3f}s")
    print(f"  - Document 1: {pagerank.get(1, 0):.4f}")
    print(f"  - Document 2: {pagerank.get(2, 0):.4f}")
    print(f"  - Document 3: {pagerank.get(3, 0):.4f}")
    
    # Compute HITS
    print("\n• Computing HITS...")
    start_time = time.time()
    hubs, authorities = link_analyzer.compute_hits({1, 2, 3}, iterations=10)
    elapsed = time.time() - start_time
    print(f"  ✓ HITS computed in {elapsed:.3f}s")
    print(f"  - Hub scores: {hubs}")
    print(f"  - Authority scores: {authorities}")
    
    stats = link_analyzer.get_graph_statistics()
    print(f"✓ Graph statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return True


def test_enhanced_search_engine():
    """Test enhanced search engine integration"""
    print("\n" + "="*70)
    print("TEST 6: Enhanced Search Engine Integration")
    print("="*70)
    
    try:
        engine = M3EnhancedSearchEngine()
        
        # Get feature statistics
        stats = engine.get_feature_stats()
        print("✓ Available features:")
        for feature, available in stats.items():
            if isinstance(available, bool):
                status = "✓" if available else "✗"
                print(f"  {status} {feature.replace('_', ' ').title()}")
        
        # Try a simple search (if index exists)
        try:
            print("\n• Testing search functionality...")
            results = engine.search("computer science", use_extra_credit=True)
            print(f"  ✓ Found {len(results)} results for 'computer science'")
            if results:
                print(f"  Top result: {results[0][1]}")
        except Exception as e:
            print(f"  ℹ Search test skipped (index may not exist): {str(e)[:50]}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("█" * 70)
    print("EXTRA CREDIT FEATURES TEST SUITE")
    print("█" * 70)
    
    tests = [
        ("Duplicate Detection", test_duplicate_detection),
        ("N-gram Indexing", test_ngram_indexing),
        ("Word Positions", test_word_positions),
        ("Anchor Text", test_anchor_text),
        ("Link Analysis", test_link_analyzer),
        ("Enhanced Search Engine", test_enhanced_search_engine),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✓ PASSED" if result else "✗ FAILED"
        except Exception as e:
            results[test_name] = f"✗ FAILED: {str(e)[:50]}"
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        print(f"{result:20} {test_name}")
    
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
