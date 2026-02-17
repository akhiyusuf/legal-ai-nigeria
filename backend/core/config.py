from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    COUNTRY: str = "{{COUNTRY}}"
    GROQ_API_KEY: str = "{{GROQ_API_KEY}}"
    VECTOR_DB: str = "{{VECTOR_DB}}"
    DOMAIN_RESTRICTION: Optional[str] = "{{DOMAIN_RESTRICTION}}"
    
    GRAPH_DB_PATH: str = "./data/legal_graph.pkl"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    SCREENSHOT_DIR: str = "./static/screenshots"
    POPPLER_PATH: Optional[str] = None
    
    # Optional DB Settings
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENV: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_URL: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.GRAPH_DB_PATH), exist_ok=True)
os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
