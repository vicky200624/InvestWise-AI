"""
SEC EDGAR Data Service for InvestWise AI 3.0.
Fetches and processes SEC filings for RAG ingestion.
"""

import os
import logging
import time
import requests
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger('investwise')

SEC_HEADERS = {
    "User-Agent": os.environ.get('SEC_EDGAR_USER_AGENT', 'InvestWise AI contact@investwise.ai'),
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

def get_cik_from_ticker(ticker: str) -> str:
    """
    Resolve ticker to CIK number using SEC company tickers JSON.
    """
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": SEC_HEADERS["User-Agent"]}
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

def fetch_company_filings(cik: str, filing_type: str = '10-K', count: int = 5) -> list[dict]:
    """
    Fetch filing metadata from SEC submissions endpoint.
    """
    if not cik:
        return []
        
    try:
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        time.sleep(0.15) 
        
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
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
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc_name}"
                
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

def download_filing_text(filing_url: str) -> str:
    """
    Download and parse filing HTML to plain text using BeautifulSoup.
    """
    try:
        headers = {"User-Agent": SEC_HEADERS["User-Agent"]}
        time.sleep(0.15)
        
        response = requests.get(filing_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        logger.error(f"Error downloading filing text from {filing_url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks for RAG ingestion.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        
    return chunks
