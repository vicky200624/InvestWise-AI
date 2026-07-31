"""
Macroeconomic Data Service for InvestWise AI 3.0.
Fetches data from FRED (Federal Reserve Economic Data).
"""

import logging
import pandas as pd
from fredapi import Fred
from typing import Dict, Any, Optional

logger = logging.getLogger('investwise.ai.macro_data')

def get_fred_client(fred_api_key: str) -> Optional[Fred]:
    if not fred_api_key:
        logger.warning("FRED_API_KEY not provided.")
        return None
    try:
        return Fred(api_key=fred_api_key)
    except Exception as e:
        logger.error(f"Error initializing Fred client: {e}")
        return None

def fetch_fred_series(series_id: str, fred_api_key: str = "", start_date: str = None) -> pd.Series:
    """
    Fetch a specific series from FRED.
    """
    client = get_fred_client(fred_api_key)
    if not client:
        return pd.Series(dtype='float64')
        
    try:
        series = client.get_series(series_id, observation_start=start_date)
        return series
    except Exception as e:
        logger.error(f"Error fetching FRED series {series_id}: {e}")
        return pd.Series(dtype='float64')

def get_macro_snapshot(fred_api_key: str = "") -> Dict[str, Any]:
    """
    Fetch latest values for GDP, CPIAUCSL, FEDFUNDS, DGS10, UNRATE.
    """
    series_ids = {
        'GDP': 'GDP',
        'CPI': 'CPIAUCSL',
        'FEDFUNDS': 'FEDFUNDS',
        'DGS10': 'DGS10',
        'UNRATE': 'UNRATE'
    }
    
    snapshot = {}
    client = get_fred_client(fred_api_key)
    if not client:
        return snapshot
        
    for name, s_id in series_ids.items():
        try:
            series = client.get_series(s_id)
            if not series.empty:
                snapshot[name] = float(series.iloc[-1])
            else:
                snapshot[name] = None
        except Exception as e:
            logger.error(f"Error fetching macro snapshot for {s_id}: {e}")
            snapshot[name] = None
            
    return snapshot

# Note: Caching logic that used Django ORM has been removed.
# Users should pass the output of get_macro_snapshot() into their feature pipeline directly.
