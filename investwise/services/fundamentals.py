"""
Fundamental Data Service for InvestWise AI 3.0.
Fetches financial statements and ratios using Financial Modeling Prep (FMP) API,
with a yfinance fallback.
"""

import os
import logging
import requests
import yfinance as yf
from django.conf import settings

logger = logging.getLogger('investwise')

FMP_API_KEY = os.environ.get('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com"

def _fmp_request(endpoint: str, params: dict) -> list[dict] | dict:
    """
    Internal helper with rate limiting, error handling for FMP API.
    """
    if not FMP_API_KEY:
        logger.warning("FMP_API_KEY not set, falling back to yfinance where applicable.")
        raise ValueError("FMP API key missing.")

    url = f"{FMP_BASE_URL}{endpoint}"
    params['apikey'] = FMP_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 429:
            logger.warning("FMP API quota exceeded.")
            raise ValueError("FMP quota exceeded.")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching from FMP ({endpoint}): {e}")
        raise ValueError(f"FMP API request failed: {e}")

def fetch_income_statement(symbol: str, period: str = 'annual', limit: int = 5) -> list[dict]:
    """
    Fetch income statement.
    """
    try:
        data = _fmp_request(f"/api/v3/income-statement/{symbol}", {"period": period, "limit": limit})
        return data if isinstance(data, list) else []
    except ValueError:
        logger.info(f"Using yfinance fallback for income statement of {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.financials if period == 'annual' else ticker.quarterly_financials
            records = df.T.reset_index().rename(columns={'index': 'date'})
            records['date'] = records['date'].astype(str)
            return records.head(limit).to_dict(orient='records')
        except Exception as e:
            logger.error(f"yfinance fallback failed for income statement: {e}")
            return []

def fetch_balance_sheet(symbol: str, period: str = 'annual', limit: int = 5) -> list[dict]:
    """
    Fetch balance sheet.
    """
    try:
        data = _fmp_request(f"/api/v3/balance-sheet-statement/{symbol}", {"period": period, "limit": limit})
        return data if isinstance(data, list) else []
    except ValueError:
        logger.info(f"Using yfinance fallback for balance sheet of {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.balance_sheet if period == 'annual' else ticker.quarterly_balance_sheet
            records = df.T.reset_index().rename(columns={'index': 'date'})
            records['date'] = records['date'].astype(str)
            return records.head(limit).to_dict(orient='records')
        except Exception as e:
            logger.error(f"yfinance fallback failed for balance sheet: {e}")
            return []

def fetch_cash_flow(symbol: str, period: str = 'annual', limit: int = 5) -> list[dict]:
    """
    Fetch cash flow statement.
    """
    try:
        data = _fmp_request(f"/api/v3/cash-flow-statement/{symbol}", {"period": period, "limit": limit})
        return data if isinstance(data, list) else []
    except ValueError:
        logger.info(f"Using yfinance fallback for cash flow of {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.cashflow if period == 'annual' else ticker.quarterly_cashflow
            records = df.T.reset_index().rename(columns={'index': 'date'})
            records['date'] = records['date'].astype(str)
            return records.head(limit).to_dict(orient='records')
        except Exception as e:
            logger.error(f"yfinance fallback failed for cash flow: {e}")
            return []

def fetch_ratios(symbol: str) -> dict:
    """
    Fetch financial ratios.
    """
    try:
        data = _fmp_request(f"/api/v3/ratios/{symbol}", {"limit": 1})
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}
    except ValueError:
        logger.info(f"Using yfinance fallback for ratios of {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "peRatio": info.get("trailingPE"),
                "pbRatio": info.get("priceToBook"),
                "dividendYield": info.get("dividendYield"),
                "debtToEquity": info.get("debtToEquity"),
            }
        except Exception as e:
            logger.error(f"yfinance fallback failed for ratios: {e}")
            return {}

def fetch_company_profile(symbol: str) -> dict:
    """
    Fetch company profile.
    """
    try:
        data = _fmp_request(f"/api/v3/profile/{symbol}", {})
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}
    except ValueError:
        logger.info(f"Using yfinance fallback for profile of {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "companyName": info.get("shortName", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "description": info.get("longBusinessSummary", ""),
            }
        except Exception as e:
            logger.error(f"yfinance fallback failed for company profile: {e}")
            return {}
