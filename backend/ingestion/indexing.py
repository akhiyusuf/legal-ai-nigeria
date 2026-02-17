import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from ..core.config import settings
from ..models.legal import LegalChunk

class Indexer:
    """
    Handles Vector DB operations (Chroma, Pinecone, FAISS, Qdrant).
    """
    def __init__(self, db_type: str = settings.VECTOR_DB):
        self.db_type = db_type
        self.client = self._get_client()
        self.collection = self.client.get_or_create_collection(
            name="legal_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

    def _get_client(self):
        """
        Return the appropriate Vector DB client based on user choice.
        """
        if self.db_type == "chroma":
            return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        elif self.db_type == "pinecone":
            # (Requires pinecone-client package)
            import pinecone
            pinecone.init(api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENV)
            # Pinecone specific setup...
            return pinecone
        # Qdrant, etc. could be added here
        return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    def add_chunks(self, chunks: List[LegalChunk]):
        """
        Index multiple chunks in the vector DB.
        """
        ids = [c.id for c in chunks]
        texts = [c.content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        
        # Chroma handles default embedding internally if not provided
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted_results = []
        # Result mapping (Chroma specific)
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": results['distances'][0][i] if 'distances' in results else 0
            })
            
        return formatted_results
