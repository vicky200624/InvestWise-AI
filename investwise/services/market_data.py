"""
Market Data Service for InvestWise AI 3.0.
Fetches stock prices, technical indicators, and indices constituents.
"""

import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger('investwise')

def fetch_historical_prices(symbol: str, period: str = '1y') -> pd.DataFrame:
    """
    Fetch historical price data for a given symbol.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            logger.warning(f"No price data found for {symbol}")
        return df
    except Exception as e:
        logger.error(f"Error fetching prices for {symbol}: {e}")
        return pd.DataFrame()

def fetch_technical_indicators(symbol: str) -> dict:
    """
    Calculate RSI (14-day), MACD (12/26/9), Bollinger Bands (20,2),
    50-day & 200-day SMA from yfinance data using pandas.
    """
    try:
        df = fetch_historical_prices(symbol, period='2y')
        if df.empty:
            return {}

        close = df['Close']
        
        # SMAs
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=200).mean().iloc[-1]

        # RSI (14-day)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_14 = 100 - (100 / (1 + rs)).iloc[-1]

        # MACD (12/26/9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]

        # Bollinger Bands (20, 2)
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        upper_bb = (sma_20 + 2 * std_20).iloc[-1]
        lower_bb = (sma_20 - 2 * std_20).iloc[-1]

        return {
            "sma_50": float(sma_50) if not pd.isna(sma_50) else None,
            "sma_200": float(sma_200) if not pd.isna(sma_200) else None,
            "rsi_14": float(rsi_14) if not pd.isna(rsi_14) else None,
            "macd": float(macd_val) if not pd.isna(macd_val) else None,
            "macd_signal": float(signal_val) if not pd.isna(signal_val) else None,
            "bb_upper": float(upper_bb) if not pd.isna(upper_bb) else None,
            "bb_lower": float(lower_bb) if not pd.isna(lower_bb) else None,
        }
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return {}

def get_sp500_tickers() -> list[str]:
    """
    Fetch S&P 500 constituents from Wikipedia.
    """
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        logger.error(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_nifty50_tickers() -> list[str]:
    """
    Return hardcoded NIFTY-50 ticker list with .NS suffix.
    """
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBI.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ITC.NS",
        "KOTAKBANK.NS", "LT.NS", "ASIANPAINT.NS", "HCLTECH.NS", "AXISBANK.NS",
        "MARUTI.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "WIPRO.NS", "TATASTEEL.NS",
        "TITAN.NS", "BAJAJFINSV.NS", "TECHM.NS", "ADANIENT.NS", "HINDALCO.NS",
        "M&M.NS", "POWERGRID.NS", "NTPC.NS", "NESTLEIND.NS", "JSWSTEEL.NS",
        "GRASIM.NS", "ONGC.NS", "CIPLA.NS", "TATAMOTORS.NS", "SBILIFE.NS",
        "HDFCLIFE.NS", "DRREDDY.NS", "APOLLOHOSP.NS", "DIVISLAB.NS", "UPL.NS",
        "EICHERMOT.NS", "BAJAJ-AUTO.NS", "INDUSINDBK.NS", "TATACONSUM.NS", "BRITANNIA.NS",
        "BPCL.NS", "HEROMOTOCO.NS", "COALIND.NS", "ADANIPORTS.NS", "LTIM.NS"
    ]
