import os
import json
import faiss
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "leetcode_index.faiss")
METADATA_PATH = os.path.join(BASE_DIR, "leetcode_metadata.json")

# Global variables for models and indices
embedding_model = None
faiss_index = None
leetcode_metadata = None

# Topic mappings for exact matching and synonym resolution
TOPIC_MAPPING = {
    "dp": "Dynamic Programming",
    "dynamic programming": "Dynamic Programming",
    "dfs": "Depth-First Search",
    "depth first search": "Depth-First Search",
    "bfs": "Breadth-First Search",
    "breadth first search": "Breadth-First Search",
    "bst": "Binary Search Tree",
    "binary search tree": "Binary Search Tree",
    "binary tree": "Binary Tree",
    "tree": "Tree",
    "union find": "Union Find",
    "dsu": "Union Find",
    "heap": "Heap (Priority Queue)",
    "pq": "Heap (Priority Queue)",
    "priority queue": "Heap (Priority Queue)",
    "two pointers": "Two Pointers",
    "two pointer": "Two Pointers",
    "sliding window": "Sliding Window",
    "binary search": "Binary Search",
    "trie": "Trie",
    "backtracking": "Backtracking",
    "greedy": "Greedy",
    "sorting": "Sorting",
    "topological sort": "Topological Sort",
    "topo sort": "Topological Sort",
    "bit manipulation": "Bit Manipulation",
    "bitmask": "Bitmask",
    "prefix sum": "Prefix Sum",
    "segment tree": "Segment Tree",
    "binary indexed tree": "Binary Indexed Tree",
    "fenwick": "Binary Indexed Tree",
    "mst": "Minimum Spanning Tree",
    "shortest path": "Shortest Path",
    "dijkstra": "Shortest Path",
    "graph": "Graph",
    "matrix": "Matrix",
    "stack": "Stack",
    "monotonic stack": "Monotonic Stack",
    "queue": "Queue",
    "recursion": "Recursion",
    "database": "Database",
    "sql": "Database"
}

def load_resources():
    global embedding_model, faiss_index, leetcode_metadata
    
    print("Loading local SentenceTransformer model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        print("Loading FAISS index...")
        faiss_index = faiss.read_index(INDEX_PATH)
        
        print("Loading Leetcode metadata...")
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            leetcode_metadata = json.load(f)
        print("Resources loaded successfully!")
        return True
    else:
        print("FAISS index or metadata files not found. Please run ingest.py first!")
        return False

# Attempt to load resources on startup (will fail if ingest.py hasn't completed, which is handled dynamically)
try:
    load_resources()
except Exception as e:
    print(f"Startup resource load deferred: {e}")

def parse_query_for_filters(query):
    """
    Parses the user query to extract strict topic and difficulty filters.
    This guarantees accurate search results for terms like 'dp' or 'dfs'.
    """
    query_lower = query.lower().strip()
    detected_topic = None
    detected_difficulty = None
    
    # Extract difficulty
    if "easy" in query_lower:
        detected_difficulty = "Easy"
    elif "medium" in query_lower:
        detected_difficulty = "Medium"
    elif "hard" in query_lower:
        detected_difficulty = "Hard"
        
    # Extract topic by checking mappings
    # Check multi-word topics first (e.g. 'sliding window') to avoid partial word match issues
    sorted_keys = sorted(TOPIC_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        # Use boundary check or substring match depending on key format
        if key in query_lower:
            # Check if it is a whole word match or well-defined substring
            # Simple check: is it surrounded by spaces/punctuation, or matches completely
            idx = query_lower.find(key)
            # Ensure it is not part of a larger word
            start_ok = (idx == 0) or (not query_lower[idx - 1].isalnum())
            end_ok = (idx + len(key) == len(query_lower)) or (not query_lower[idx + len(key)].isalnum())
            if start_ok and end_ok:
                detected_topic = TOPIC_MAPPING[key]
                break
                
    return detected_topic, detected_difficulty

def hybrid_search(query, k=6):
    global embedding_model, faiss_index, leetcode_metadata
    
    if faiss_index is None or leetcode_metadata is None:
        # Try loading again in case ingestion finished in background
        if not load_resources():
            return []
            
    # Extract strict filters
    detected_topic, detected_difficulty = parse_query_for_filters(query)
    print(f"Query: '{query}' -> Detected Topic: '{detected_topic}', Detected Difficulty: '{detected_difficulty}'")
    
    # 1. FAISS Search
    query_vector = embedding_model.encode([query], convert_to_numpy=True).astype('float32')
    faiss.normalize_L2(query_vector)
    
    # Search a larger candidate pool to filter
    candidate_k = min(150, len(leetcode_metadata))
    scores, indices = faiss_index.search(query_vector, candidate_k)
    
    candidates = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(leetcode_metadata):
            continue
        item = leetcode_metadata[idx]
        candidates.append((float(score), item))
        
    # 2. Score/Re-rank candidates based on strict topic and difficulty matching
    ranked_candidates = []
    for score, item in candidates:
        has_topic_match = False
        has_diff_match = False
        
        # Check topic match (exact check in the problem's topic list)
        if detected_topic:
            # Check case-insensitive similarity or exact match
            has_topic_match = any(detected_topic.lower() == t.lower() for t in item.get('topics', []))
        
        # Check difficulty match
        if detected_difficulty:
            has_diff_match = (detected_difficulty.lower() == item.get('difficulty', '').lower())
            
        # Assign ranking category score
        # 3: matches both topic and difficulty
        # 2: matches topic only (when topic was requested)
        # 1: matches difficulty only (when difficulty was requested) or matches neither but no filters requested
        # 0: fails the topic match if a topic was explicitly requested (strict filtering!)
        if detected_topic and not has_topic_match:
            continue
            
        # Determine priority group
        if detected_topic and detected_difficulty:
            group = 3 if (has_topic_match and has_diff_match) else (2 if has_topic_match else 1)
        elif detected_topic:
            group = 2 if has_topic_match else 0
        elif detected_difficulty:
            group = 2 if has_diff_match else 1
        else:
            group = 1
            
        ranked_candidates.append({
            "group": group,
            "score": score,
            "item": item
        })
        
    # Sort by group (descending, higher group is better) and then by FAISS score (descending)
    ranked_candidates.sort(key=lambda x: (-x['group'], -x['score']))
    
    # Return top K
    results = [c['item'] for c in ranked_candidates[:k]]
    
    # Fallback: if strict filtering returned too few results, fill up with standard FAISS results
    if len(results) < k and not detected_topic:
        existing_ids = {r['id'] for r in results}
        for _, item in candidates:
            if len(results) >= k:
                break
            if item['id'] not in existing_ids:
                results.append(item)
                existing_ids.add(item['id'])
                
    return results

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json or {}
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400
        
    k = data.get('k', 6)
    results = hybrid_search(query, k=k)
    return jsonify({"results": results})

# Read your Gemini API Key from the environment. DO NOT hardcode secrets in source.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    query = data.get('message', '')
    if not query:
        return jsonify({"error": "Message cannot be empty"}), 400
        
    client_api_key = GEMINI_API_KEY if (GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE") else os.environ.get("GEMINI_API_KEY")
    if not client_api_key:
        return jsonify({
            "error": "Gemini API Key is not configured. Set the GEMINI_API_KEY environment variable (do not commit secrets)."
        }), 400
        
    # 1. Retrieve relevant problems
    retrieved_problems = hybrid_search(query, k=6)
    
    # 2. Build context for Gemini
    context = "Here are the top retrieved Leetcode problems related to the user's query:\n\n"
    if not retrieved_problems:
        context += "No matching problems found in the dataset.\n"
    else:
        for idx, p in enumerate(retrieved_problems):
            context += f"Problem {idx+1}: {p['title']}\n"
            context += f"- Link: {p['link']}\n"
            context += f"- Difficulty: {p['difficulty']}\n"
            context += f"- Topics: {', '.join(p['topics']) if p['topics'] else 'None'}\n"
            context += f"- Acceptance Rate: {p['acceptance_rate']}%\n"
            context += f"- Likes/Dislikes: {p['likes']} Likes, {p['dislikes']} Dislikes\n"
            context += f"- Category: {p['category']}\n\n"
            
    # 3. Call Gemini
    try:
        system_instruction = (
            "You are LeetGPT, a world-class Leetcode pattern expert, data structures & algorithms instructor, "
            "and technical interview coach. You have deep knowledge of optimal algorithmic approaches, patterns "
            "(e.g., sliding window, fast/slow pointers, Monotonic Stack, DP state transitions), and time/space complexity.\n\n"
            "Guidelines:\n"
            "1. Be extremely accurate. If the user asks about a specific pattern (like DP), focus purely on that pattern.\n"
            "2. When explaining, reference the retrieved problems explicitly. Use their exact names and explain how they "
            "fit into the pattern/concept.\n"
            "3. Format your response beautifully using Markdown. Use bold headers, lists, and wrap code snippets in standard "
            "fenced code blocks (e.g., ```python, ```cpp, ```javascript) with comments explaining key steps.\n"
            "4. Analyze the time and space complexity of the proposed solutions.\n"
            "5. Keep the tone professional, encouraging, and highly technical."
        )
        
        # Try multiple model candidates in sequence to handle model-specific rate limits and quotas
        model_candidates = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest", "gemini-pro-latest"]
        
        response = None
        last_error = None
        
        prompt = f"User Query: {query}\n\n{context}\n\nPlease answer the user query based on the retrieved Leetcode context above."
        
        genai.configure(api_key=client_api_key)
        
        for model_name in model_candidates:
            try:
                print(f"Attempting to generate response with: {model_name}...")
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.2}
                )
                # Success, break loop
                print(f"Success with model: {model_name}!")
                break
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                last_error = e
                
        if response is None:
            raise last_error if last_error else Exception("All model generation attempts failed.")
            
        answer = response.text
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate response from Gemini API: {str(e)}"}), 500
        
    return jsonify({
        "answer": answer,
        "problems": retrieved_problems
    })

@app.route('/api/topics', methods=['GET'])
def api_topics():
    global leetcode_metadata
    if leetcode_metadata is None:
        if not load_resources():
            return jsonify({"topics": []})
            
    # Compile a unique list of topics
    unique_topics = set()
    for item in leetcode_metadata:
        for topic in item.get('topics', []):
            unique_topics.add(topic)
            
    return jsonify({"topics": sorted(list(unique_topics))})

@app.route('/api/status', methods=['GET'])
def api_status():
    global faiss_index, leetcode_metadata
    loaded = (faiss_index is not None and leetcode_metadata is not None)
    return jsonify({
        "status": "ready" if loaded else "loading/missing_index",
        "total_problems": len(leetcode_metadata) if leetcode_metadata else 0
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
