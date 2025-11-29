"""
Web-based Search Interface for M3 (uses M3EnhancedSearchEngine)
"""
import os
import sys
import time
from flask import Flask, render_template, request, jsonify

# Ensure project SRC is on path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from search_engine_enhanced import M3EnhancedSearchEngine

app = Flask(__name__, template_folder='templates')

# Initialize search engine
index_dir = os.path.join(script_dir, '..', 'index')

if not os.path.exists(index_dir):
    print(f"Error: Index directory not found: {index_dir}")
    print("Please ensure the index has been built.")
    sys.exit(1)

print("Initializing M3 enhanced search engine...")
try:
    search_engine = M3EnhancedSearchEngine(index_dir)
    print("Search engine ready!")
except Exception as e:
    print(f"Error initializing search engine: {e}")
    sys.exit(1)


@app.route('/')
def index():
    return render_template('search.html')


@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Please enter a query'})

        start = time.time()
        results = search_engine.search(query)
        elapsed = (time.time() - start) * 1000.0

        # Format results
        out = []
        for rank, (doc_id, url, score) in enumerate(results[:10], start=1):
            out.append({'rank': rank, 'url': url, 'score': score})

        return jsonify({'success': True, 'results': out, 'query_time_ms': elapsed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/features')
def features():
    try:
        stats = search_engine.get_feature_stats()
        return jsonify({'success': True, 'features': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run M3 web search server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Run Flask in debug mode')
    args = parser.parse_args()

    # Start the Flask app with provided host/port
    print(f"Starting web server on {args.host}:{args.port} (debug={args.debug})")
    app.run(host=args.host, port=args.port, debug=args.debug)
