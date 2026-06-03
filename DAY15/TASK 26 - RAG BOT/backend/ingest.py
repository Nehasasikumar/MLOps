import os
import json
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "Leetcode.csv")
INDEX_PATH = os.path.join(BASE_DIR, "leetcode_index.faiss")
METADATA_PATH = os.path.join(BASE_DIR, "leetcode_metadata.json")

def ingest_data():
    print(f"Reading dataset from {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Leetcode.csv not found at {CSV_PATH}")
    
    df = pd.read_csv(CSV_PATH)
    
    # Fill NaN values for easier processing
    df['Topics'] = df['Topics'].fillna('')
    df['Category'] = df['Category'].fillna('Algorithms')
    df['Likes'] = df['Likes'].fillna(0).astype(int)
    df['Dislikes'] = df['Dislikes'].fillna(0).astype(int)
    df['Acceptance Rate (%)'] = df['Acceptance Rate (%)'].fillna(50.0)
    df['Difficulty'] = df['Difficulty'].fillna('Medium')
    df['Premium Only'] = df['Premium Only'].fillna(False)
    
    print(f"Total problems loaded: {len(df)}")
    
    # Prepare text for embedding and build structured metadata list
    documents = []
    metadata_list = []
    
    for idx, row in df.iterrows():
        # Text to embed
        doc_text = f"Problem: {row['Title']}\n" \
                   f"Difficulty: {row['Difficulty']}\n" \
                   f"Category: {row['Category']}\n" \
                   f"Topics: {row['Topics']}\n" \
                   f"Acceptance Rate: {row['Acceptance Rate (%)']}%\n" \
                   f"Likes: {row['Likes']}, Dislikes: {row['Dislikes']}"
        documents.append(doc_text)
        
        # Metadata to save for UI display
        metadata_list.append({
            "id": int(row['ID']) if 'ID' in row and pd.notna(row['ID']) else idx,
            "title": str(row['Title']),
            "difficulty": str(row['Difficulty']),
            "link": str(row['Link']) if 'Link' in row else "",
            "topics": [t.strip() for t in str(row['Topics']).split(',') if t.strip()] if row['Topics'] else [],
            "acceptance_rate": float(row['Acceptance Rate (%)']),
            "premium_only": bool(row['Premium Only']),
            "category": str(row['Category']),
            "likes": int(row['Likes']),
            "dislikes": int(row['Dislikes'])
        })
        
    print("Loading embedding model (all-MiniLM-L6-v2) locally...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings for Leetcode problems... (this may take a minute)")
    embeddings = model.encode(documents, show_progress_bar=True, convert_to_numpy=True)
    
    # Ensure float32 for FAISS
    embeddings = embeddings.astype('float32')
    dimension = embeddings.shape[1]
    
    print(f"Creating FAISS index with dimension {dimension}...")
    index = faiss.IndexFlatIP(dimension)  # IndexFlatIP uses Inner Product
    
    # Normalize vectors for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    # Save the index
    print(f"Saving FAISS index to {INDEX_PATH}...")
    faiss.write_index(index, INDEX_PATH)
    
    # Save metadata
    print(f"Saving metadata to {METADATA_PATH}...")
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    # Make sure backend folder exists
    os.makedirs(BASE_DIR, exist_ok=True)
    ingest_data()
