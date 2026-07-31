"""
Fundamental Data Service for InvestWise AI 3.0.
Fetches financial statements and ratios using Financial Modeling Prep (FMP) API,
with a yfinance fallback.
"""

import logging
import requests
try:
    import yfinance as yf
except ImportError:
    yf = None
from typing import List, Dict, Any, Union, Optional

logger = logging.getLogger('investwise.ai.fundamentals')

def _fmp_request(endpoint: str, params: dict, fmp_api_key: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Internal helper with rate limiting, error handling for FMP API.
    """
    if not fmp_api_key:
        logger.warning("FMP_API_KEY not set, falling back to yfinance where applicable.")
        raise ValueError("FMP API key missing.")

    fmp_base_url = "https://financialmodelingprep.com"
    url = f"{fmp_base_url}{endpoint}"
    params['apikey'] = fmp_api_key
    
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

def fetch_income_statement(symbol: str, fmp_api_key: str = "", period: str = 'annual', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch income statement.
    """
    try:
        data = _fmp_request(f"/api/v3/income-statement/{symbol}", {"period": period, "limit": limit}, fmp_api_key)
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

def fetch_balance_sheet(symbol: str, fmp_api_key: str = "", period: str = 'annual', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch balance sheet.
    """
    try:
        data = _fmp_request(f"/api/v3/balance-sheet-statement/{symbol}", {"period": period, "limit": limit}, fmp_api_key)
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

def fetch_cash_flow(symbol: str, fmp_api_key: str = "", period: str = 'annual', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch cash flow statement.
    """
    try:
        data = _fmp_request(f"/api/v3/cash-flow-statement/{symbol}", {"period": period, "limit": limit}, fmp_api_key)
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

def fetch_ratios(symbol: str, fmp_api_key: str = "") -> Dict[str, Any]:
    """
    Fetch financial ratios.
    """
    try:
        data = _fmp_request(f"/api/v3/ratios/{symbol}", {"limit": 1}, fmp_api_key)
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

def fetch_company_profile(symbol: str, fmp_api_key: str = "") -> Dict[str, Any]:
    """
    Fetch company profile.
    """
    try:
        data = _fmp_request(f"/api/v3/profile/{symbol}", {}, fmp_api_key)
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

def calculate_piotroski_score(current_year: Dict[str, Any], prior_year: Optional[Dict[str, Any]] = None) -> int:
    """
    Calculate 0-9 Piotroski F-Score for financial strength assessment.
    """
    score = 0
    try:
        net_income = float(current_year.get("netIncome", 0))
        total_assets = float(current_year.get("totalAssets", 1)) or 1.0
        operating_cf = float(current_year.get("operatingCashFlow", current_year.get("netCashProvidedByOperatingActivities", 0)))
        
        # 1. Positive Net Income
        if net_income > 0:
            score += 1
        # 2. Positive ROA
        roa = net_income / total_assets
        if roa > 0:
            score += 1
        # 3. Positive Operating Cash Flow
        if operating_cf > 0:
            score += 1
        # 4. Cash Flow > Net Income (Quality of earnings)
        if operating_cf > net_income:
            score += 1
            
        if prior_year:
            # 5. Lower leverage
            curr_lt_debt = float(current_year.get("longTermDebt", 0)) / total_assets
            prior_assets = float(prior_year.get("totalAssets", 1)) or 1.0
            prior_lt_debt = float(prior_year.get("longTermDebt", 0)) / prior_assets
            if curr_lt_debt <= prior_lt_debt:
                score += 1
                
            # 6. Higher current ratio
            curr_cr = float(current_year.get("currentRatio", 1.5))
            prior_cr = float(prior_year.get("currentRatio", 1.5))
            if curr_cr > prior_cr:
                score += 1
                
            # 7. No share dilution
            curr_shares = float(current_year.get("weightedAverageShsOut", 1))
            prior_shares = float(prior_year.get("weightedAverageShsOut", 1))
            if curr_shares <= prior_shares:
                score += 1
                
            # 8. Higher gross margin
            curr_gm = float(current_year.get("grossProfit", 0)) / (float(current_year.get("revenue", 1)) or 1.0)
            prior_gm = float(prior_year.get("grossProfit", 0)) / (float(prior_year.get("revenue", 1)) or 1.0)
            if curr_gm > prior_gm:
                score += 1
                
            # 9. Higher asset turnover
            curr_at = float(current_year.get("revenue", 0)) / total_assets
            prior_at = float(prior_year.get("revenue", 0)) / prior_assets
            if curr_at > prior_at:
                score += 1
        else:
            # Default heuristics if prior year not available
            score += 3 # Assign neutral mid-score for YoY comparisons
            
    except Exception as e:
        logger.warning(f"Error calculating Piotroski F-Score: {e}")
    return min(9, max(0, score))

def calculate_altman_z_score(financials: Dict[str, Any]) -> float:
    """
    Calculate Altman Z-Score for bankruptcy risk predicting:
    Z = 1.2A + 1.4B + 3.3C + 0.6D + 0.999E
    """
    try:
        total_assets = float(financials.get("totalAssets", 1000000)) or 1.0
        total_liabilities = float(financials.get("totalLiabilities", 500000)) or 1.0
        working_capital = float(financials.get("totalCurrentAssets", 0)) - float(financials.get("totalCurrentLiabilities", 0))
        retained_earnings = float(financials.get("retainedEarnings", 0))
        ebit = float(financials.get("ebit", financials.get("operatingIncome", 0)))
        market_cap = float(financials.get("marketCap", float(financials.get("totalStockholdersEquity", 1000000))))
        sales = float(financials.get("revenue", 0))
        
        a = working_capital / total_assets
        b = retained_earnings / total_assets
        c = ebit / total_assets
        d = market_cap / total_liabilities
        e = sales / total_assets
        
        z = (1.2 * a) + (1.4 * b) + (3.3 * c) + (0.6 * d) + (0.999 * e)
        return round(z, 2)
    except Exception as e:
        logger.warning(f"Error calculating Altman Z-Score: {e}")
        return 3.0 # Default safe zone

