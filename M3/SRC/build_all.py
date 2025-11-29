"""
Build All - Master index builder script
Builds everything sequentially: core index + all extra-credit features
"""

import os
import sys
import subprocess
import time


class BuildAll:
    """Master builder that runs all builders sequentially"""
    
    def __init__(self, data_dir, index_dir):
        """Initialize builder"""
        self.data_dir = os.path.abspath(data_dir)
        self.index_dir = os.path.abspath(index_dir)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.builders = [
            ('build_core_index.py', 'Core Index'),
            ('build_duplicates.py', 'Duplicate Detection'),
            ('build_ngrams.py', 'N-gram Indexing'),
            ('build_positions.py', 'Word Positions'),
            ('build_anchors.py', 'Anchor Text'),
            ('build_links.py', 'Link Analysis'),
        ]
    
    def run_builder(self, script_name, display_name):
        """Run a single builder script"""
        script_path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"✗ Script not found: {script_path}")
            return False
        
        print(f"\n{'=' * 80}")
        print(f"Running: {display_name}")
        print(f"{'=' * 80}")
        
        try:
            cmd = [
                sys.executable,
                script_path,
                self.data_dir,
                self.index_dir
            ]
            
            result = subprocess.run(cmd, check=True)
            return result.returncode == 0
        
        except subprocess.CalledProcessError as e:
            print(f"✗ {display_name} failed with error code {e.returncode}")
            return False
        except Exception as e:
            print(f"✗ {display_name} failed: {str(e)}")
            return False
    
    def build_all(self):
        """Build all indices sequentially"""
        print("\n" + "=" * 80)
        print("M3 SEARCH ENGINE - COMPLETE INDEX BUILDER")
        print("=" * 80)
        print(f"\nData Directory: {self.data_dir}")
        print(f"Index Directory: {self.index_dir}")
        print(f"\nBuilders to run: {len(self.builders)}")
        for _, display_name in self.builders:
            print(f"  → {display_name}")
        
        print("\n" + "=" * 80)
        print("Starting build process...")
        print("=" * 80)
        
        # Validate inputs
        if not os.path.exists(self.data_dir):
            print(f"\n✗ ERROR: Data directory not found: {self.data_dir}")
            return False
        
        # Create index directory if needed
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Run each builder
        successful = []
        failed = []
        
        start_time = time.time()
        
        for script_name, display_name in self.builders:
            builder_start = time.time()
            success = self.run_builder(script_name, display_name)
            builder_time = time.time() - builder_start
            
            if success:
                successful.append(f"{display_name} ({builder_time:.1f}s)")
            else:
                failed.append(f"{display_name} ({builder_time:.1f}s)")
        
        total_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 80)
        print("BUILD SUMMARY")
        print("=" * 80)
        
        print(f"\nSuccessful ({len(successful)}/{len(self.builders)}):")
        for item in successful:
            print(f"  ✓ {item}")
        
        if failed:
            print(f"\nFailed ({len(failed)}):")
            for item in failed:
                print(f"  ✗ {item}")
        
        print(f"\nTotal time: {total_time:.1f} seconds")
        
        # Verify features
        print(f"\n" + "=" * 80)
        print("Verifying indices...")
        print("=" * 80)
        
        verify_script = os.path.join(self.script_dir, 'verify_features.py')
        if os.path.exists(verify_script):
            try:
                subprocess.run(
                    [sys.executable, verify_script, self.index_dir],
                    check=True
                )
            except subprocess.CalledProcessError:
                pass
        
        print("\n" + "=" * 80)
        if not failed:
            print("✓ ALL BUILDS COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Start web interface: python web_search_m3.py")
            print("  2. Visit: http://127.0.0.1:5001")
            print("  3. Test search functionality")
            return True
        else:
            print("✗ SOME BUILDS FAILED")
            print("=" * 80)
            print("\nTo build individual features, run:")
            print("  python build_core_index.py ../Data ../index")
            print("  python build_duplicates.py ../Data ../index")
            print("  python build_ngrams.py ../Data ../index")
            print("  python build_positions.py ../Data ../index")
            print("  python build_anchors.py ../Data ../index")
            print("  python build_links.py ../Data ../index")
            return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python build_all.py <data_directory> [index_directory]")
        print("\nExample:")
        print("  python build_all.py ../Data ../index")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    index_dir = sys.argv[2] if len(sys.argv) > 2 else 'index'
    
    builder = BuildAll(data_dir, index_dir)
    success = builder.build_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
