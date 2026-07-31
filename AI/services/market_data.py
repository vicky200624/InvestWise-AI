"""
Market Data Service for InvestWise AI 3.0.
Fetches stock prices, technical indicators, and indices constituents.
"""

import logging
import pandas as pd
import yfinance as yf
from typing import List, Dict, Any

logger = logging.getLogger('investwise.ai.market_data')

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

def fetch_technical_indicators(symbol: str) -> Dict[str, Any]:
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
        middle_bb = sma_20.iloc[-1]

        # ATR (14-day)
        high = df['High']
        low = df['Low']
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.rolling(window=14).mean().iloc[-1]

        # ADX (14-day approximation)
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        plus_di = 100 * (plus_dm.rolling(14).mean() / (tr.rolling(14).mean() + 1e-9))
        minus_di = 100 * (minus_dm.rolling(14).mean() / (tr.rolling(14).mean() + 1e-9))
        dx = 100 * ((plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-9))
        adx_14 = dx.rolling(14).mean().iloc[-1]

        # Momentum & Volatility
        momentum_10 = (close.iloc[-1] / close.iloc[-11] - 1.0) * 100 if len(close) > 10 else 0.0
        volatility_30d = close.pct_change().rolling(30).std().iloc[-1] * (252 ** 0.5)

        # Support & Resistance (20-day min/max)
        support_level = low.rolling(window=20).min().iloc[-1]
        resistance_level = high.rolling(window=20).max().iloc[-1]

        return {
            "sma_50": float(sma_50) if not pd.isna(sma_50) else None,
            "sma_200": float(sma_200) if not pd.isna(sma_200) else None,
            "rsi_14": float(rsi_14) if not pd.isna(rsi_14) else None,
            "macd": float(macd_val) if not pd.isna(macd_val) else None,
            "macd_signal": float(signal_val) if not pd.isna(signal_val) else None,
            "bb_upper": float(upper_bb) if not pd.isna(upper_bb) else None,
            "bb_middle": float(middle_bb) if not pd.isna(middle_bb) else None,
            "bb_lower": float(lower_bb) if not pd.isna(lower_bb) else None,
            "atr_14": float(atr_14) if not pd.isna(atr_14) else 0.0,
            "adx_14": float(adx_14) if not pd.isna(adx_14) else 0.0,
            "momentum_10": float(momentum_10) if not pd.isna(momentum_10) else 0.0,
            "volatility_30d": float(volatility_30d) if not pd.isna(volatility_30d) else 0.0,
            "support_level": float(support_level) if not pd.isna(support_level) else None,
            "resistance_level": float(resistance_level) if not pd.isna(resistance_level) else None,
        }
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return {}

def get_sp500_tickers() -> List[str]:
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

def get_nifty50_tickers() -> List[str]:
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
