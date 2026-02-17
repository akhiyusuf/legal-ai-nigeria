import os
import sys
import logging
from pypdf import PdfReader
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.ingestion.chunking import StructureAwareChunker
from backend.ingestion.indexing import Indexer
from backend.ingestion.graph import KnowledgeGraphBuilder
from backend.models.legal import LegalChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_pdf(file_path: str, chunker: StructureAwareChunker, indexer: Indexer, kg_builder: KnowledgeGraphBuilder):
    logger.info(f"Processing {file_path}...")
    
    try:
        reader = PdfReader(file_path)
        filename = os.path.basename(file_path)
        
        # Basic metadata
        metadata = {
            "law_type": "statute",
            "source_url": f"local://{filename}",
            "title": filename.replace(".pdf", "").replace("_", " "),
            "jurisdiction": settings.COUNTRY,
            "date": datetime.now().isoformat(),
        }

        all_chunks = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            
            # OCR Fallback if text extraction fails
            if not text or len(text.strip()) < 50:
                logger.info(f"Page {i+1} of {filename} seems to be an image. Attempting OCR...")
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
                    logger.error(f"OCR failed for {filename} page {i+1}: {ocr_e}")
            
            if not text or len(text.strip()) < 10:
                continue
            
            page_meta = metadata.copy()
            page_meta["page_number"] = i + 1
            # Ensure unique IDs by adding page number to the source_url base used for IDs
            page_meta["source_url"] = f"local://{filename}#page={i+1}"
            
            # Chunking (this preserves headers if patterns match)
            chunks = chunker.chunk_text(text, page_meta)
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning(f"No content extracted from {filename}")
            return

        logger.info(f"Extracted {len(all_chunks)} chunks from {filename}")
        
        # Add to Vector DB
        indexer.add_chunks(all_chunks)
        
        # Add to Knowledge Graph
        for chunk in all_chunks:
            kg_builder.extract_and_add(chunk)
            
    except Exception as e:
        logger.error(f"Error ingesting {file_path}: {e}")

def main():
    data_dir = os.path.join("data", "nigeria_laws")
    if not os.path.exists(data_dir):
        logger.error(f"Data directory {data_dir} not found.")
        return

    chunker = StructureAwareChunker()
    indexer = Indexer()
    kg_builder = KnowledgeGraphBuilder()

    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(data_dir, filename)
            ingest_pdf(file_path, chunker, indexer, kg_builder)

    kg_builder.save_graph()
    logger.info("Ingestion of local laws complete.")

if __name__ == "__main__":
    main()
