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
        # Format Context with a clear separator
        context_str = ""
        for i, c in enumerate(context_chunks):
            context_str += f"--- SOURCE {i+1} ---\n"
            context_str += f"ID: {c['id']}\n"
            context_str += f"TITLE: {c['metadata'].get('title')}\n"
            context_str += f"SECTION: {c['metadata'].get('section_ref', 'N/A')}\n"
            context_str += f"PAGE: {c['metadata'].get('page_number', 'N/A')}\n"
            context_str += f"CONTENT: {c['content']}\n\n"
        
        system_prompt = f"""
        You are a highly professional Legal Assistant for {settings.COUNTRY} laws.
        You will be provided with specific legal context (SOURCE 1, SOURCE 2, etc.).
        
        ### MANDATORY INSTRUCTIONS:
        1. SYNTHESIZE a clear, helpful answer to the user's question based ONLY on the provided SOURCES.
        2. DO NOT just list or repeat the sources. Write a cohesive legal explanation.
        3. CITE your sources inline using the exact ID format: [ID: ID_VALUE].
           Example: "...as stated in the Constitution [ID: local://Constitution.pdf#page=5]."
        4. If the provided sources do not contain the answer, say: "I'm sorry, but I couldn't find specific information regarding that in my current legal database."
        5. NEVER use the internal reasoning tags (like [[ DOCUMENT | LOCATION ]]) in your final response.
        6. MAINTAIN a formal yet helpful tone.
        
        ### LEGAL CONTEXT (SOURCES):
        {context_str}
        
        ### DISCLAIMER:
        "This information is for informational purposes only and is not legal advice."
        """

        messages = [{"role": "system", "content": system_prompt}]
        # Add history (last 5 messages)
        messages.extend(history[-5:])
        messages.append({"role": "user", "content": query})

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2 # Slightly higher for better synthesis
            )
            
            answer = chat_completion.choices[0].message.content
            
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
                "answer": answer,
                "citations": citations
            }
        except Exception as e:
            logging.error("Groq API call failed", exc_info=True)
            return {"error": str(e), "answer": "I apologize, but I encountered an error while processing your request. Please try again or ask another question.", "citations": []}
