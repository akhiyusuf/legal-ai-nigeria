from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict, Any
import uvicorn
import os
import logging
from .core.config import settings
from .models.legal import QueryRequest, AnswerResponse
from .retrieval.engine import HybridRetrievalEngine
from .services.groq_service import GroqService
from .services.screenshot_service import ScreenshotService
from .ingestion.discovery import SourceDiscovery
from .ingestion.chunking import StructureAwareChunker
from .ingestion.graph import KnowledgeGraphBuilder
from .ingestion.indexing import Indexer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="Legal AI RAG System", description=f"QA System for {settings.COUNTRY} Laws")

# Serve static files for UI and screenshots
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Global services (Lazy initialization)
retrieval_engine = None
groq_service = None
screenshot_service = None

def init_services():
    global retrieval_engine, groq_service, screenshot_service
    retrieval_engine = HybridRetrievalEngine()
    groq_service = GroqService()
    screenshot_service = ScreenshotService()

@app.on_event("startup")
async def startup_event():
    # If the vector DB/Graph doesn't exist, we might need to run ingestion.
    # For now, just initialize services.
    init_services()
    
    # Start Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_update, 'cron', hour=2) # 2 AM Daily
    scheduler.start()

@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

# Global state for context (In-memory, reset on server restart)
session_contexts = {}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QueryRequest):
    """
    Core RAG query handler with follow-up support.
    """
    if not retrieval_engine:
        raise HTTPException(status_code=500, detail="Retrieval engine not initialized.")
        
    # 1. Analyze if new search is needed
    analysis = groq_service.analyze_query(request.query, request.history)
    
    retrieved = None
    if analysis.get('search_needed', True):
        # Use rewritten query if available
        search_query = analysis.get('search_query', request.query)
        retrieved = retrieval_engine.retrieve(search_query, top_k=request.top_k)
        
        # 2. Sort results (Ascending: Title, then Section, then Page)
        retrieved['top_k_chunks'].sort(key=lambda x: (
            str(x['metadata'].get('title', '')),
            str(x['metadata'].get('section_ref', '') or ''),
            int(x['metadata'].get('page_number', 0))
        ))
        
        # Store context for simple session tracking (using query as key)
        session_contexts[request.query] = retrieved
    else:
        # Try to find context from last interaction
        last_query = request.history[-2]['content'] if len(request.history) >= 2 else ""
        retrieved = session_contexts.get(last_query, {"top_k_chunks": [], "graph_context": []})

    # 3. Extract graph paths
    graph_paths = [f"{n['id']} ({n['data'].get('type')})" for n in retrieved.get('graph_context', [])]
    
    # 4. Generate answer via Groq with history
    print(f"DEBUG: Processing query: {request.query}")
    print(f"DEBUG: History length: {len(request.history)}")
    
    response = groq_service.generate_answer(
        query=request.query,
        context_chunks=retrieved.get('top_k_chunks', []),
        graph_paths=graph_paths,
        history=request.history
    )
    
    print(f"DEBUG: Generated Answer: {response.get('answer')[:100]}...")
    
    return AnswerResponse(
        answer=response['answer'],
        citations=response['citations'],
        graph_paths=[[p] for p in graph_paths]
    )

@app.get("/proof")
async def get_proof(doc_url: str, page: int):
    """
    Returns screenshot of a specific legal source page.
    """
    path = screenshot_service.generate_screenshot(doc_url, page)
    if not path:
        raise HTTPException(status_code=404, detail="Screenshot could not be generated.")
    return FileResponse(path)

@app.post("/admin/ingest")
async def start_ingestion(background_tasks: BackgroundTasks):
    """
    Trigger initial ingestion for {{COUNTRY}}.
    """
    background_tasks.add_task(run_full_ingestion)
    return {"status": "Ingestion started in background"}

@app.post("/admin/update")
async def trigger_update():
    """
    Manual update trigger.
    """
    run_update()
    return {"status": "Update completed"}

# --- Ingestion & Update Logic ---

def run_full_ingestion():
    logging.info(f"Starting ingestion of local laws for {settings.COUNTRY}...")
    data_dir = os.path.join("data", "nigeria_laws")
    if not os.path.exists(data_dir):
        logging.error(f"Data directory {data_dir} not found.")
        return

    chunker = StructureAwareChunker()
    indexer = Indexer()
    kg_builder = KnowledgeGraphBuilder()
    
    from pypdf import PdfReader
    from datetime import datetime
    import pytesseract
    from pdf2image import convert_from_path

    for filename in os.listdir(data_dir):
        if not filename.endswith(".pdf"):
            continue
            
        file_path = os.path.join(data_dir, filename)
        logging.info(f"Processing {file_path}...")
        
        try:
            reader = PdfReader(file_path)
            # Basic metadata
            metadata = {
                "law_type": "statute",
                "source_url": f"local://{filename}", # Base for IDs
                "title": filename.replace(".pdf", "").replace("_", " "),
                "jurisdiction": settings.COUNTRY,
                "date": datetime.now().isoformat(),
            }

            all_chunks = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                
                # OCR Fallback
                if not text or len(text.strip()) < 50:
                    try:
                        images = convert_from_path(
                            file_path,
                            first_page=i+1,
                            last_page=i+1,
                            poppler_path=settings.POPPLER_PATH if settings.POPPLER_PATH else None
                        )
                        if images:
                            text = pytesseract.image_to_string(images[0])
                    except Exception as ocr_e:
                        logging.error(f"OCR failed for {filename} page {i+1}: {ocr_e}")

                if not text or len(text.strip()) < 10:
                    continue
                
                page_meta = metadata.copy()
                page_meta["page_number"] = i + 1
                # Ensure unique IDs
                page_meta["source_url"] = f"local://{filename}#page={i+1}"
                
                chunks = chunker.chunk_text(text, page_meta)
                all_chunks.extend(chunks)

            if all_chunks:
                indexer.add_chunks(all_chunks)
                for chunk in all_chunks:
                    kg_builder.extract_and_add(chunk)
                logging.info(f"Indexed {len(all_chunks)} chunks from {filename}")
            else:
                logging.warning(f"No text extracted from {filename}")
                
        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")
                
    kg_builder.save_graph()
    logging.info("Full ingestion complete.")

def run_update():
    """
    Daily polling update.
    """
    logging.info("Checking for legal updates...")
    # 1. Discover sources again
    # 2. Compare against existing knowledge
    # 3. Add new ones
    pass

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
