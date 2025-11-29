"""
Verify Features - Check which indices are populated
Diagnostic tool to show status of all extra-credit features
"""

import json
import os
import sys
from pathlib import Path


class FeatureVerifier:
    """Verifies which extra-credit features have been built"""
    
    def __init__(self, index_dir='index'):
        """Initialize verifier"""
        self.index_dir = index_dir
        
        self.features = {
            'core_inverted_index': {
                'file': 'inverted_index.json',
                'description': 'Core: Inverted Index (required)',
                'required': True
            },
            'core_doc_mapping': {
                'file': 'doc_mapping.json',
                'description': 'Core: Document Mapping (required)',
                'required': True
            },
            'duplicate_detection': {
                'file': 'duplicates.json',
                'description': 'Extra Credit #1: Duplicate Detection',
                'required': False
            },
            'ngram_index': {
                'file': ['bigram_index.json', 'trigram_index.json'],
                'description': 'Extra Credit #2: N-gram Indexing',
                'required': False
            },
            'word_positions': {
                'file': 'word_positions.json',
                'description': 'Extra Credit #3: Word Positions',
                'required': False
            },
            'anchor_text': {
                'file': 'anchor_text_index.json',
                'description': 'Extra Credit #4: Anchor Text',
                'required': False
            },
            'link_analysis': {
                'file': ['pagerank.json', 'hits.json'],
                'description': 'Extra Credit #5: Link Analysis (PageRank & HITS)',
                'required': False
            }
        }
    
    def check_file_status(self, file_path):
        """Check if file exists and has real data"""
        if not os.path.exists(file_path):
            return {
                'exists': False,
                'size': 0,
                'populated': False,
                'status': 'MISSING'
            }
        
        try:
            size = os.path.getsize(file_path)
            
            # Check if it's a stub (very small file)
            if size < 100:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content.strip() == '{}' or content.strip() == '[]':
                    return {
                        'exists': True,
                        'size': size,
                        'populated': False,
                        'status': 'STUB (empty)'
                    }
            
            # Try to load and check content
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine if populated
            is_populated = False
            if isinstance(data, dict):
                is_populated = len(data) > 0
            elif isinstance(data, list):
                is_populated = len(data) > 0
            
            status = 'POPULATED' if is_populated else 'EMPTY'
            
            return {
                'exists': True,
                'size': size,
                'populated': is_populated,
                'status': status
            }
        
        except Exception as e:
            return {
                'exists': True,
                'size': size,
                'populated': False,
                'status': f'ERROR: {str(e)}'
            }
    
    def verify(self):
        """Verify all features"""
        print("\n" + "=" * 80)
        print("FEATURE VERIFICATION REPORT")
        print("=" * 80)
        print(f"\nIndex Directory: {os.path.abspath(self.index_dir)}\n")
        
        # Create index dir if it doesn't exist
        if not os.path.exists(self.index_dir):
            print(f"ERROR: Index directory not found: {self.index_dir}")
            return False
        
        # Check each feature
        all_core_present = True
        extra_credit_status = {}
        
        for feature_key, feature_info in self.features.items():
            files = feature_info['file']
            if isinstance(files, str):
                files = [files]
            
            print(f"{feature_info['description']}")
            
            all_files_ok = True
            for file_name in files:
                file_path = os.path.join(self.index_dir, file_name)
                status = self.check_file_status(file_path)
                
                # Format output
                symbol = '✓' if status['populated'] else '✗'
                size_str = f"{status['size'] / (1024*1024):.2f} MB" if status['size'] > 1024*1024 else f"{status['size']} bytes"
                
                print(f"  {symbol} {file_name:<30} {status['status']:<25} {size_str}")
                
                if feature_info['required'] and not status['populated']:
                    all_core_present = False
                
                if not feature_info['required']:
                    extra_credit_status[feature_key] = status['populated']
                
                all_files_ok = all_files_ok and status['populated']
            
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if all_core_present:
            print("✓ Core indices: COMPLETE")
        else:
            print("✗ Core indices: INCOMPLETE - Run build_core_index.py first")
        
        extra_credit_count = sum(1 for v in extra_credit_status.values() if v)
        total_extra_credit = len(extra_credit_status)
        
        print(f"✓ Extra-Credit features: {extra_credit_count}/{total_extra_credit} populated")
        
        for feature_key, populated in extra_credit_status.items():
            feature_info = self.features[feature_key]
            symbol = '✓' if populated else '○'
            print(f"  {symbol} {feature_info['description']}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDED NEXT STEPS")
        print("=" * 80)
        
        if not all_core_present:
            print("1. Build core index:")
            print("   python build_core_index.py ../Data ../index")
        else:
            print("1. Core index ready ✓")
        
        if extra_credit_count < total_extra_credit:
            print("\n2. Build missing extra-credit features:")
            if not extra_credit_status.get('duplicate_detection', False):
                print("   python build_duplicates.py ../Data ../index")
            if not extra_credit_status.get('ngram_index', False):
                print("   python build_ngrams.py ../Data ../index")
            if not extra_credit_status.get('word_positions', False):
                print("   python build_positions.py ../Data ../index")
            if not extra_credit_status.get('anchor_text', False):
                print("   python build_anchors.py ../Data ../index")
            if not extra_credit_status.get('link_analysis', False):
                print("   python build_links.py ../Data ../index")
        else:
            print("\n2. All features complete ✓")
        
        print("\n3. Test the web search interface:")
        print("   python web_search_m3.py")
        print("   Then visit: http://127.0.0.1:5001")
        
        print("\n" + "=" * 80 + "\n")
        
        return all_core_present


def main():
    """Main function"""
    index_dir = sys.argv[1] if len(sys.argv) > 1 else 'index'
    
    verifier = FeatureVerifier(index_dir)
    success = verifier.verify()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
