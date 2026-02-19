import spacy
from sentence_transformers import CrossEncoder, SentenceTransformer
import os

def download_models():
    # 1. Download SpaCy model
    print("Downloading SpaCy model 'en_core_web_sm'...")
    try:
        spacy.cli.download("en_core_web_sm")
    except Exception as e:
        print(f"Error downloading SpaCy: {e}")

    # 2. Download Cross-Encoder (Reranker)
    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    print(f"Downloading Cross-Encoder '{model_name}'...")
    try:
        CrossEncoder(model_name)
    except Exception as e:
        print(f"Error downloading Cross-Encoder: {e}")

    # 3. Download ChromaDB default embedding model
    # (Typically all-MiniLM-L6-v2)
    embedding_model = "all-MiniLM-L6-v2"
    print(f"Downloading Embedding model '{embedding_model}'...")
    try:
        SentenceTransformer(embedding_model)
    except Exception as e:
        print(f"Error downloading Embedding model: {e}")

if __name__ == "__main__":
    download_models()
