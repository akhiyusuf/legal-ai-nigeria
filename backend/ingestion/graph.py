import networkx as nx
import spacy
from typing import List, Dict, Any
import logging
import pickle
import os
from ..models.legal import LegalChunk, Entity
from ..core.config import settings

class KnowledgeGraphBuilder:
    """
    Builds a lightweight legal knowledge graph from documents.
    """
    def __init__(self, load_path: str = settings.GRAPH_DB_PATH):
        self.load_path = load_path
        self.graph = nx.DiGraph()
        # Initialize spaCy NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # Fallback if model not downloaded (should be handled by requirements)
            logging.warning("SpaCy model not found. Downloading...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        # Add basic labels for legal NER (simulated or simplified)
        # In a real legal system, we'd use a specialized model like Blackstone or Legal-BERT
        self.legal_labels = ["LAW", "COURT", "ORG", "GPE", "PERSON", "DATE", "STATUTE", "PROVISION"]

    def extract_and_add(self, chunk: LegalChunk):
        """
        Extract entities from chunk and update graph.
        """
        doc = self.nlp(chunk.content)
        
        # 1. Add node for the chunk itself
        self.graph.add_node(chunk.id, type="CHUNK", content=chunk.content[:200], metadata=chunk.metadata)
        
        # 2. Extract entities (spacy default + custom patterns)
        entities = []
        for ent in doc.ents:
            if ent.label_ in ["LAW", "ORG", "GPE", "DATE"]: # Basic mapping
                entities.append((ent.text, ent.label_))
        
        # 3. Add section-level links
        section_ref = chunk.metadata.get('section_ref')
        if section_ref:
            self.graph.add_node(section_ref, type="SECTION", title=chunk.metadata.get('title'))
            self.graph.add_edge(chunk.id, section_ref, relation="PART_OF")
            
        # 4. Add law-level links (Title/Act)
        title = chunk.metadata.get('title')
        if title:
            self.graph.add_node(title, type="STATUTE")
            if section_ref:
                self.graph.add_edge(section_ref, title, relation="CONTAINED_IN")

        # 5. Link extracted entities
        for ent_name, ent_type in entities:
            self.graph.add_node(ent_name, type=ent_type)
            self.graph.add_edge(chunk.id, ent_name, relation="MENTIONS")

    def save_graph(self):
        with open(self.load_path, 'wb') as f:
            pickle.dump(self.graph, f)

    def load_graph(self):
        if os.path.exists(self.load_path):
            with open(self.load_path, 'rb') as f:
                self.graph = pickle.load(f)
        return self.graph

    def get_related_nodes(self, entity_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Traverse the graph to find relevant nodes for multi-hop reasoning.
        """
        if entity_name not in self.graph:
            return []
            
        nodes = []
        # Basic BFS
        visited = set()
        queue = [(entity_name, 0)]
        while queue:
            curr, d = queue.pop(0)
            if d > depth or curr in visited:
                continue
            visited.add(curr)
            
            data = self.graph.nodes[curr]
            nodes.append({"id": curr, "data": data})
            
            for neighbor in self.graph.neighbors(curr):
                queue.append((neighbor, d + 1))
                
        return nodes
