# Legal QA System: Advanced RAG for {{COUNTRY}}

A production-ready Legal Question Answering system utilizing Advanced Retrieval-Augmented Generation (RAG).

## Features
- **Structure-Aware Chunking**: Preserves titles, chapters, and sections.
- **Knowledge Graph**: Entity extraction (spaCy) and NetworkX graph for multi-hop reasoning.
- **Hybrid Retrieval**: Combines Vector Search (Chroma) and Graph Traversal.
- **Reranking**: Uses Cross-Encoders for precision.
- **Source Proof**: Screenshot generation for PDF sources using `pdf2image`.
- **Auto-Discovery**: Automatic discovery of official legal portals for {{COUNTRY}}.

## Prerequisites
- Python 3.10+
- Poppler (system dependency for `pdf2image`)
  - Linux: `sudo apt-get install poppler-utils`
  - Mac: `brew install poppler`

## Installation
1. Clone the repository and navigate to the directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
3. Configure your environment in `.env`:
   ```env
   GROQ_API_KEY=your_key
   COUNTRY={{COUNTRY}}
   VECTOR_DB={{VECTOR_DB}}
   ```

## Getting Started
1. **Initial Ingestion**:
   Run the ingestion script to discover and index laws for {{COUNTRY}}.
   ```bash
   # Trigger via API
   curl -X POST http://localhost:8000/admin/ingest
   ```

2. **Run the Application**:
   ```bash
   python -m backend.main
   ```
   Open `http://localhost:8000` in your browser.

## Architecture
1. **Discovery**: `SourceDiscovery` identifies official .gov domains.
2. **Indexing**: Chunks are stored in ChromaDB; Entities are stored in a NetworkX graph.
3. **Retrieval**: 
   - Semantic search finds similar text.
   - Graph traversal finds related provisions (multi-hop).
   - Results are fused and reranked by a MiniLM Cross-Encoder.
4. **Generation**: Groq (Mixtral) generates answers grounded in the retrieved context with citations.

## Disclaimer
This tool is for informational purposes only. It is NOT a substitute for professional legal advice.
