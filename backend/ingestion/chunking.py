import re
from typing import List, Dict, Any, Optional
from ..models.legal import LegalMetadata, LegalChunk

class StructureAwareChunker:
    """
    Advanced chunker that tracks hierarchical legal structures (Parts, Chapters, Sections, etc.)
    regardless of the specific law's organization style.
    """
    
    # Patterns for various hierarchical levels
    HIERARCHY_PATTERNS = [
        (r"(?i)^(PART)\s+([IVXLCDM\d]+|[\w\s]+)", "Part"),
        (r"(?i)^(CHAPTER)\s+([IVXLCDM\d]+)", "Chapter"),
        (r"(?i)^(TITLE)\s+([IVXLCDM\d]+)", "Title"),
        (r"(?i)^(SECTION|ARTICLE|CLAUSE|REGULATION)\s+(\d+)", "Provision"),
        (r"^§\s*(\d+)", "Provision"),
        (r"(?i)^([A-Z\s]{5,})$", "Heading") # Catch all caps lines as potential headers
    ]

    def __init__(self, chunk_size: int = 1500, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[LegalChunk]:
        chunks = []
        lines = text.split('\n')
        current_chunk_lines = []
        current_size = 0
        
        # State tracking for hierarchy
        hierarchy_state = {
            "Part": None,
            "Chapter": None,
            "Provision": None,
            "Heading": None
        }

        chunk_id_base = metadata.get('source_url', 'chunk')

        for line in lines:
            line_strip = line.strip()
            if not line_strip: continue

            # 1. Detect hierarchy changes
            found_header = False
            for pattern, level in self.HIERARCHY_PATTERNS:
                match = re.match(pattern, line_strip)
                if match:
                    # If it's a new main provision, flush the current chunk
                    if level in ["Provision", "Part", "Chapter"] and current_chunk_lines:
                        chunks.append(self._make_enhanced_chunk(current_chunk_lines, hierarchy_state, metadata, chunk_id_base, len(chunks)))
                        current_chunk_lines = current_chunk_lines[-2:] if len(current_chunk_lines) > 2 else []
                        current_size = sum(len(l) for l in current_chunk_lines)

                    hierarchy_state[level] = line_strip
                    # Clear sub-levels when a higher level changes
                    if level == "Part": 
                        hierarchy_state["Chapter"] = hierarchy_state["Provision"] = hierarchy_state["Heading"] = None
                    elif level == "Chapter":
                        hierarchy_state["Provision"] = hierarchy_state["Heading"] = None
                    elif level == "Provision":
                        hierarchy_state["Heading"] = None
                    
                    found_header = True
                    break

            current_chunk_lines.append(line)
            current_size += len(line)

            # 2. Flush if size limit reached
            if current_size >= self.chunk_size:
                chunks.append(self._make_enhanced_chunk(current_chunk_lines, hierarchy_state, metadata, chunk_id_base, len(chunks)))
                current_chunk_lines = current_chunk_lines[-3:] # Small overlap
                current_size = sum(len(l) for l in current_chunk_lines)

        # Final flush
        if current_chunk_lines:
            chunks.append(self._make_enhanced_chunk(current_chunk_lines, hierarchy_state, metadata, chunk_id_base, len(chunks)))

        return chunks

    def _make_enhanced_chunk(self, lines: List[str], state: Dict[str, Optional[str]], meta: Dict[str, Any], base_id: str, index: int) -> LegalChunk:
        raw_content = "\n".join(lines).strip()
        
        # Build Breadcrumb Path
        path_elements = []
        if state["Part"]: path_elements.append(state["Part"])
        if state["Chapter"]: path_elements.append(state["Chapter"])
        if state["Provision"]: path_elements.append(state["Provision"])
        if state["Heading"]: path_elements.append(state["Heading"])
        
        path_str = " > ".join(path_elements) if path_elements else "General Provisions"
        doc_title = meta.get('title', 'Legal Document')
        
        # Format for AI: Heavy grounding header
        enhanced_content = f"[[ DOCUMENT: {doc_title} | LOCATION: {path_str} ]]\n\n{raw_content}"
        
        new_meta = meta.copy()
        new_meta['hierarchy_path'] = path_str
        new_meta['section_ref'] = state["Provision"] or state["Heading"] or "N/A"
        
        return LegalChunk(
            id=f"{base_id}_{index}",
            content=enhanced_content,
            metadata=new_meta
        )
