"""
News Sentiment Service for InvestWise AI 3.0.
Fetches news from Finnhub and calculates sentiment using FinBERT.
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger('investwise')

FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

_FINBERT_PIPELINE = None

def _get_finbert_pipeline():
    """
    Get or initialize the FinBERT pipeline lazily.
    """
    global _FINBERT_PIPELINE
    if _FINBERT_PIPELINE is None:
        try:
            from transformers import pipeline
            logger.info("Loading FinBERT pipeline for sentiment analysis...")
            _FINBERT_PIPELINE = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            logger.error(f"Failed to load FinBERT pipeline: {e}")
            raise e
    return _FINBERT_PIPELINE

def fetch_company_news(symbol: str, from_date: str, to_date: str) -> list[dict]:
    """
    Fetch company news from Finnhub.
    """
    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set.")
        return []
        
    try:
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching company news for {symbol}: {e}")
        return []

def fetch_general_news(category: str = 'general') -> list[dict]:
    """
    Fetch general market news from Finnhub.
    """
    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set.")
        return []

    try:
        url = f"{FINNHUB_BASE_URL}/news"
        params = {
            "category": category,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching general news: {e}")
        return []

def analyze_sentiment(texts: list[str]) -> list[dict]:
    """
    Analyze sentiment of a list of texts using FinBERT.
    Returns list of dicts with text, label (positive, negative, neutral), and score.
    """
    if not texts:
        return []
        
    try:
        pipeline = _get_finbert_pipeline()
        truncated_texts = [text[:512] for text in texts]
        results = pipeline(truncated_texts)
        
        output = []
        for text, result in zip(texts, results):
            output.append({
                "text": text,
                "label": result['label'],
                "score": result['score']
            })
        return output
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return []

def get_market_sentiment_score(symbol: str, days: int = 7) -> dict:
    """
    Fetch recent news, run FinBERT, return aggregated sentiment score and breakdown.
    """
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    news = fetch_company_news(symbol, from_date, to_date)
    if not news:
        return {"aggregate_score": 0, "positive": 0, "negative": 0, "neutral": 0, "total": 0}
        
    headlines = [item.get('headline', '') for item in news if item.get('headline')]
    sentiments = analyze_sentiment(headlines)
    
    if not sentiments:
        return {"aggregate_score": 0, "positive": 0, "negative": 0, "neutral": 0, "total": 0}
        
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    weighted_score = 0
    
    for s in sentiments:
        label = s['label']
        counts[label] += 1
        if label == 'positive':
            weighted_score += s['score']
        elif label == 'negative':
            weighted_score -= s['score']
            
    total = len(sentiments)
    aggregate_score = weighted_score / total if total > 0 else 0
    
    return {
        "aggregate_score": aggregate_score,
        "positive": counts["positive"],
        "negative": counts["negative"],
        "neutral": counts["neutral"],
        "total": total
    }
