"""
RAG Retrieval module.
"""
import logging
from typing import List, Dict, Any
from AI.services import rag_engine

logger = logging.getLogger('investwise.ai.rag.retrieval')

def search(query: str, ticker: str, n_results: int = 5, persist_dir: str = './chroma_db') -> List[Dict[str, Any]]:
    """Search ingested documents for a given ticker."""
    collection_name = f"sec_{ticker.upper()}"
    results = rag_engine.query_documents(query, collection_name, n_results, persist_dir=persist_dir)
    return results
