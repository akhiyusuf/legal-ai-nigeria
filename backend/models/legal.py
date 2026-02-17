from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class LegalChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class LegalMetadata(BaseModel):
    law_type: str  # e.g., criminal, civil, constitutional
    source_url: str
    title: str
    jurisdiction: str
    date: datetime
    section_ref: Optional[str] = None
    page_number: Optional[int] = None

class Entity(BaseModel):
    name: str
    type: str  # e.g., STATUTE, COURT, CONCEPT
    relationships: List[Dict[str, str]] = []

class AnswerResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    graph_paths: Optional[List[List[str]]] = None

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    top_k: int = 5
