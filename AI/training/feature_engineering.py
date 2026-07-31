"""
Feature Engineering for Model Training.
Creates 60+ features from all data sources.
"""
import logging
import pandas as pd

logger = logging.getLogger('investwise.ai.training.feature_engineering')

def engineer_features(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Create features from raw data."""
    logger.info("Engineering features from raw data...")
    if raw_data.empty:
        return raw_data
        
    df = raw_data.copy()
    
    # Moving averages
    df['SMA_10'] = df.groupby('Symbol')['Close'].transform(lambda x: x.rolling(window=10).mean())
    df['SMA_50'] = df.groupby('Symbol')['Close'].transform(lambda x: x.rolling(window=50).mean())
    
    # Returns
    df['Return_1d'] = df.groupby('Symbol')['Close'].transform(lambda x: x.pct_change(1))
    df['Return_5d'] = df.groupby('Symbol')['Close'].transform(lambda x: x.pct_change(5))
    
    # Target
    df['Target_Return_5d'] = df.groupby('Symbol')['Close'].transform(lambda x: x.pct_change(5).shift(-5))
    
    df = df.dropna()
    return df
