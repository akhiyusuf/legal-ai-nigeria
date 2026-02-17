import os
import sys
import logging

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.retrieval.engine import HybridRetrievalEngine

logging.basicConfig(level=logging.INFO)

def main():
    try:
        engine = HybridRetrievalEngine()
        query = "What is the jurisdiction of the Supreme Court in the Constitution?"
        print(f"Query: {query}")
        
        results = engine.retrieve(query, top_k=3)
        
        print("\n--- Top Retrieved Chunks ---")
        for i, chunk in enumerate(results['top_k_chunks']):
            print(f"\n[{i+1}] ID: {chunk['id']}")
            print(f"Title: {chunk['metadata'].get('title')}")
            print(f"Section: {chunk['metadata'].get('section_ref')}")
            print(f"Content (truncated): {chunk['content'][:300]}...")

        print("\n--- Graph Context ---")
        for node in results['graph_context']:
            print(f"Node: {node['id']} ({node['data'].get('type')})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
