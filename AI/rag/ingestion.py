"""
RAG Ingestion Pipeline.
"""
import logging
from typing import List, Dict, Any
from AI.services import rag_engine, sec_edgar

logger = logging.getLogger('investwise.ai.rag.ingestion')

def ingest_sec_filings(ticker: str, cik: str, persist_dir: str = './chroma_db') -> int:
    """Download SEC filings and ingest into RAG."""
    logger.info(f"Ingesting SEC filings for {ticker}")
    filings = sec_edgar.fetch_company_filings(cik)
    if not filings:
        return 0
        
    total_chunks = 0
    collection_name = f"sec_{ticker.upper()}"
    
    for filing in filings:
        text = sec_edgar.download_filing_text(filing['url'])
        if text:
            chunks = sec_edgar.chunk_text(text)
            metadata = {"symbol": ticker, "form": filing['form'], "date": filing['date']}
            count = rag_engine.ingest_document(chunks, metadata, collection_name, persist_dir=persist_dir)
            total_chunks += count
            
    return total_chunks
