"""
SEC EDGAR Data Service for InvestWise AI 3.0.
Fetches and processes SEC filings for RAG ingestion.
"""

import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

logger = logging.getLogger('investwise.ai.sec_edgar')

def _get_sec_headers(user_agent: str) -> Dict[str, str]:
    return {
        "User-Agent": user_agent or 'InvestWise AI contact@investwise.ai',
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov"
    }

def get_cik_from_ticker(ticker: str, user_agent: str = "") -> str:
    """
    Resolve ticker to CIK number using SEC company tickers JSON.
    """
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": _get_sec_headers(user_agent)["User-Agent"]}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        ticker = ticker.upper()
        for key, val in data.items():
            if val.get("ticker") == ticker:
                return str(val.get("cik_str")).zfill(10)
        
        logger.warning(f"CIK not found for ticker {ticker}")
        return ""
    except Exception as e:
        logger.error(f"Error resolving ticker to CIK: {e}")
        return ""

def fetch_company_filings(cik: str, filing_type: str = '10-K', count: int = 5, user_agent: str = "") -> List[Dict[str, Any]]:
    """
    Fetch filing metadata from SEC submissions endpoint.
    """
    if not cik:
        return []
        
    try:
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        time.sleep(0.15) 
        
        response = requests.get(url, headers=_get_sec_headers(user_agent), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        recent_filings = data.get("filings", {}).get("recent", {})
        if not recent_filings:
            return []
            
        forms = recent_filings.get("form", [])
        accessions = recent_filings.get("accessionNumber", [])
        primary_docs = recent_filings.get("primaryDocument", [])
        dates = recent_filings.get("filingDate", [])
        
        results = []
        found = 0
        for i, form in enumerate(forms):
            if form == filing_type:
                acc_no = accessions[i].replace("-", "")
                doc_name = primary_docs[i]
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{str(int(cik))}/{acc_no}/{doc_name}"
                
                results.append({
                    "form": form,
                    "date": dates[i],
                    "url": filing_url
                })
                found += 1
                if found >= count:
                    break
                    
        return results
    except Exception as e:
        logger.error(f"Error fetching filings for CIK {cik}: {e}")
        return []

def download_filing_text(filing_url: str, user_agent: str = "") -> str:
    """
    Download and parse filing HTML to plain text using BeautifulSoup.
    """
    try:
        headers = {"User-Agent": _get_sec_headers(user_agent)["User-Agent"]}
        time.sleep(0.15)
        
        response = requests.get(filing_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        logger.error(f"Error downloading filing text from {filing_url}: {e}")
        return ""

def chunk_text(text: str, chunk_tokens: int = 1000, overlap_tokens: int = 175) -> List[str]:
    """
    Split text into overlapping chunks for RAG ingestion.
    Per Part 2 spec: Chunk Size 800-1200 tokens, Overlap 150-200 tokens.
    Uses ~4 characters per token as standard heuristic when tokenizer is offline.
    """
    if not text:
        return []
        
    char_size = chunk_tokens * 4
    char_overlap = overlap_tokens * 4
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + char_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += char_size - char_overlap
        
    return chunks

def build_chunk_metadata(
    company: str,
    year: str,
    quarter: str,
    doc_type: str,
    section: str = "General",
    page: int = 1,
    source_url: str = ""
) -> Dict[str, Any]:
    """
    Build structured RAG chunk metadata per Part 2 spec:
    Company, Year, Quarter, Document Type, Section, Page Number, Source URL.
    """
    return {
        "company": company.upper(),
        "year": str(year),
        "quarter": str(quarter),
        "document_type": doc_type,
        "section": section,
        "page_number": int(page),
        "source_url": source_url,
    }

