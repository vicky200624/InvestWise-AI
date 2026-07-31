"""
Macroeconomic Data Service for InvestWise AI 3.0.
Fetches data from FRED (Federal Reserve Economic Data) and manages caching.
"""

import os
import logging
import pandas as pd
from fredapi import Fred
from investwise.models import MacroIndicator
from django.conf import settings

logger = logging.getLogger('investwise')

FRED_API_KEY = os.environ.get('FRED_API_KEY')

def get_fred_client():
    if not FRED_API_KEY:
        logger.warning("FRED_API_KEY not set.")
        return None
    try:
        return Fred(api_key=FRED_API_KEY)
    except Exception as e:
        logger.error(f"Error initializing Fred client: {e}")
        return None

def fetch_fred_series(series_id: str, start_date: str = None) -> pd.Series:
    """
    Fetch a specific series from FRED.
    """
    client = get_fred_client()
    if not client:
        return pd.Series(dtype='float64')
        
    try:
        series = client.get_series(series_id, observation_start=start_date)
        return series
    except Exception as e:
        logger.error(f"Error fetching FRED series {series_id}: {e}")
        return pd.Series(dtype='float64')

def get_macro_snapshot() -> dict:
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
    client = get_fred_client()
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

def cache_macro_data() -> int:
    """
    Persist all macro indicators to the MacroIndicator Django model.
    """
    snapshot = get_macro_snapshot()
    count = 0
    try:
        from django.utils import timezone
        today = timezone.now().date()

        for name, value in snapshot.items():
            if value is not None:
                MacroIndicator.objects.update_or_create(
                    indicator_code=name,
                    date=today,
                    defaults={
                        'indicator_name': name,
                        'value': value,
                        'source': 'FRED',
                    }
                )
                count += 1
        return count
    except Exception as e:
        logger.error(f"Error caching macro data: {e}")
        return count

def get_cached_macro_features() -> dict:
    """
    Read from MacroIndicator model for ML feature engineering.
    Returns latest value for each indicator code.
    """
    features = {}
    try:
        # Get the latest value for each indicator
        from django.db.models import Max
        latest_dates = MacroIndicator.objects.values('indicator_code').annotate(
            latest_date=Max('date')
        )
        for entry in latest_dates:
            indicator = MacroIndicator.objects.filter(
                indicator_code=entry['indicator_code'],
                date=entry['latest_date']
            ).first()
            if indicator:
                features[indicator.indicator_code] = indicator.value
        return features
    except Exception as e:
        logger.error(f"Error reading cached macro features: {e}")
        return features
