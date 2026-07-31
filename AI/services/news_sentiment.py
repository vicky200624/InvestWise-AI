"""
News Sentiment Service for InvestWise AI 3.0.
Fetches news from Finnhub and calculates sentiment using FinBERT.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger('investwise.ai.news_sentiment')

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
            logger.warning(f"Failed to load FinBERT pipeline ({e}), using fallback heuristic sentiment.")
            _FINBERT_PIPELINE = "FALLBACK"
    return _FINBERT_PIPELINE

def fetch_company_news(symbol: str, from_date: str, to_date: str, finnhub_api_key: str = "") -> List[Dict[str, Any]]:
    """
    Fetch company news from Finnhub.
    """
    if not finnhub_api_key:
        logger.warning("FINNHUB_API_KEY not set.")
        return []
        
    try:
        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": finnhub_api_key
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching company news for {symbol}: {e}")
        return []

def fetch_general_news(category: str = 'general', finnhub_api_key: str = "") -> List[Dict[str, Any]]:
    """
    Fetch general market news from Finnhub.
    """
    if not finnhub_api_key:
        logger.warning("FINNHUB_API_KEY not set.")
        return []

    try:
        url = "https://finnhub.io/api/v1/news"
        params = {
            "category": category,
            "token": finnhub_api_key
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching general news: {e}")
        return []

def analyze_sentiment(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze sentiment of a list of texts using FinBERT or fallback financial lexicon.
    Returns list of dicts with text, label ('positive', 'negative', 'neutral'), and score.
    """
    if not texts:
        return []
        
    try:
        pipeline = _get_finbert_pipeline()
        if pipeline == "FALLBACK" or pipeline is None:
            # Financial keyword heuristic fallback
            pos_words = {"growth", "profit", "surge", "gain", "beat", "strong", "bullish", "record", "dividend"}
            neg_words = {"loss", "decline", "drop", "miss", "weak", "bearish", "lawsuit", "debt", "warning"}
            output = []
            for text in texts:
                lower = text.lower()
                p_count = sum(1 for w in pos_words if w in lower)
                n_count = sum(1 for w in neg_words if w in lower)
                if p_count > n_count:
                    output.append({"text": text, "label": "positive", "score": 0.85})
                elif n_count > p_count:
                    output.append({"text": text, "label": "negative", "score": 0.85})
                else:
                    output.append({"text": text, "label": "neutral", "score": 0.70})
            return output

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

def get_finbert_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate 768-dimensional FinBERT embeddings for news or report chunks.
    """
    if not texts:
        return []
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        model = AutoModel.from_pretrained("ProsusAI/finbert")
        inputs = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            # Use CLS token embedding
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy().tolist()
        return embeddings
    except Exception as e:
        logger.warning(f"FinBERT embedding generation fallback: {e}")
        return [[0.0] * 768 for _ in texts]


def get_market_sentiment_score(symbol: str, days: int = 7, finnhub_api_key: str = "") -> Dict[str, Any]:
    """
    Fetch recent news, run FinBERT, return aggregated sentiment score and breakdown.
    """
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    news = fetch_company_news(symbol, from_date, to_date, finnhub_api_key)
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
