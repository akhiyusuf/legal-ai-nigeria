try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

from typing import List, Dict, Any
import logging
from ..ingestion.indexing import Indexer
from ..ingestion.graph import KnowledgeGraphBuilder
from ..core.config import settings

class HybridRetrievalEngine:
    """
    Combined vector and graph-based retrieval with reranking.
    """
    def __init__(self, vector_db: str = settings.VECTOR_DB):
        self.indexer = Indexer(db_type=vector_db)
        self.kg = KnowledgeGraphBuilder()
        self.kg.load_graph() # Load existing graph
        
        # Initialize Cross-Encoder for reranking
        if CrossEncoder:
            try:
                self.reranker = CrossEncoder(settings.RERANKER_MODEL)
            except Exception as e:
                logging.error(f"Error loading reranker: {e}")
                self.reranker = None
        else:
            self.reranker = None

    def retrieve(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Hybrid search + Graph + Rerank.
        """
        # 1. Vector Search (Semantic)
        vector_results = self.indexer.search(query, top_k=top_k * 2)
        
        # 2. Graph Traversal (Contextual)
        # Extract entities from query for graph starting points
        query_doc = self.kg.nlp(query)
        graph_results = []
        for ent in query_doc.ents:
            # Multi-hop retrieval: traverse 2 steps
            related = self.kg.get_related_nodes(ent.text, depth=2)
            # Filter for CHUNK types
            graph_results.extend([
                {
                    "id": node['id'],
                    "content": node['data'].get('content', ''),
                    "metadata": node['data'].get('metadata', {}),
                    "score": 0.5 # Default heuristic score for graph hits
                } for node in related if node['data'].get('type') == 'CHUNK'
            ])
            
        # 3. Combine and Deduplicate
        seen_ids = set()
        combined_results = []
        for res in vector_results + graph_results:
            if res['id'] not in seen_ids:
                combined_results.append(res)
                seen_ids.add(res['id'])
                
        # 4. Reranking (Cross-Encoder)
        if self.reranker and combined_results:
            # Pair query with each content
            pairs = [[query, r['content']] for r in combined_results]
            scores = self.reranker.predict(pairs)
            
            # Update scores and sort
            for i, score in enumerate(scores):
                combined_results[i]['rerank_score'] = float(score)
                
            combined_results.sort(key=lambda x: x['rerank_score'], reverse=True)
        else:
            # Fallback sort by vector score if reranker unavailable
            combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        return {
            "top_k_chunks": combined_results[:top_k],
            "graph_context": [res for res in graph_results if res['id'] in seen_ids][:5]
        }
