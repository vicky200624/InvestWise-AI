"""
Data Pipeline for Model Training.
Fetches and cleans historical data.
"""
import logging
import pandas as pd
from typing import List

from AI.services import market_data

logger = logging.getLogger('investwise.ai.training.data_pipeline')

def fetch_and_clean_data(symbols: List[str], period: str = '5y') -> pd.DataFrame:
    """Fetch historical data for multiple symbols and clean it."""
    logger.info(f"Fetching data for {symbols} over {period}")
    all_data = []
    
    for symbol in symbols:
        try:
            df = market_data.fetch_historical_prices(symbol, period=period)
            if not df.empty:
                df['Symbol'] = symbol
                all_data.append(df)
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            
    if all_data:
        combined = pd.concat(all_data)
        combined = combined.dropna()
        return combined
    return pd.DataFrame()
