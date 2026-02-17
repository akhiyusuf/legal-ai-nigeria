from groq import Groq
import os
from typing import List, Dict, Any
import json
import logging
from ..core.config import settings

class GroqService:
    """
    Interfaces with Groq models for legal generation.
    """
    def __init__(self, api_key: str = settings.GROQ_API_KEY):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def analyze_query(self, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Decides if a new search is needed.
        """
        if not history:
            return {"search_needed": True, "search_query": query}
            
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])
        
        system_prompt = f"""
        Analyze the user's latest query in the context of our legal conversation.
        Decide if a new search for legal documents is needed or if this is a direct follow-up 
        based on the previous context provided.
        
        Respond ONLY with a JSON object: 
        {{"search_needed": boolean, "search_query": "Rewritten search query or empty if not needed"}}
        
        Conversation Context:
        {history_str}
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            analysis = json.loads(completion.choices[0].message.content)
            print(f"DEBUG: Search Analysis: {analysis}")
            return analysis
        except Exception as e:
            logging.error(f"Query analysis failed: {e}")
            return {"search_needed": True, "search_query": query}

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]], graph_paths: List[str], history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        """
        Produce a grounded answer with citations.
        """
        # Format Context
        context_str = "\n\n".join([
            f"ID: {c['id']}\nTitle: {c['metadata'].get('title')}\nSection: {c['metadata'].get('section_ref')}\nContent: {c['content']}" 
            for c in context_chunks
        ])
        
        # Format Graph context (e.g., entity relationships)
        graph_str = "\n".join(graph_paths)
        
        system_prompt = f"""
        You are an expert legal assistant specialized in the laws of {settings.COUNTRY}.
        Your goal is to answer the user's question using the provided legal context.
        
        ### Rules:
        1. Base your answer ONLY on the provided context. If unsure, state it.
        2. ALWAYS cite the source using the exact ID provided in the context: [ID: ID_HERE].
           Example: [ID: local://doc.pdf#page=1]
        3. ACCURACY IS CRITICAL: Use the [[ DOCUMENT | LOCATION ]] tag at the start of each chunk for your internal reasoning to identify the correct Part and Section.
        4. **CRITICAL**: DO NOT include the [[ DOCUMENT | LOCATION ]] tag in your final response to the user. Use only your own words and [ID: ...] citations.
        5. Use a formal, legal tone but remain accessible.
        
        ### Context:
        {context_str}
        
        ### Disclaimer:
        "This information is for informational purposes only and is not legal advice."
        """

        messages = [{"role": "system", "content": system_prompt}]
        # Add history (last 5 messages to avoid token limit)
        messages.extend(history[-5:])
        messages.append({"role": "user", "content": query})

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.1
            )
            
            # Map citations
            citations = [
                {
                    "id": c['id'],
                    "title": c['metadata'].get('title'),
                    "url": c['metadata'].get('source_url'),
                    "section": c['metadata'].get('section_ref'),
                    "page": c['metadata'].get('page_number')
                } for c in context_chunks
            ]
            
            return {
                "answer": chat_completion.choices[0].message.content,
                "citations": citations
            }
        except Exception as e:
            logging.error("Groq API call failed", exc_info=True)
            return {"error": str(e), "answer": "An error occurred during generation.", "citations": []}
