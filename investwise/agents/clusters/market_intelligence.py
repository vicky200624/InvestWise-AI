import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from investwise.agents.state import InvestmentAnalysisState

logger = logging.getLogger('investwise')

def fetch_news(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Fetching news for %s", state['stock_symbol'])
    return {
        "current_step": "Fetching company news",
        "market_intelligence": {"news": ["Company reports strong earnings", "New product launch"]}
    }

def sentiment_analysis(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Analyzing sentiment for %s", state['stock_symbol'])
    market = state.get("market_intelligence", {}) or {}
    market["sentiment"] = "positive"
    return {
        "current_step": "Analyzing news sentiment",
        "market_intelligence": market
    }

def macro_context(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Fetching macro context")
    market = state.get("market_intelligence", {}) or {}
    market["macro_regime"] = "expansionary"
    return {
        "current_step": "Assessing macro regime",
        "market_intelligence": market
    }

def competitor_ranking(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Ranking competitors for %s", state['stock_symbol'])
    market = state.get("market_intelligence", {}) or {}
    market["competitor_rank"] = "top quartile"
    return {
        "current_step": "Ranking sector competitors",
        "market_intelligence": market
    }

def score_sentiment(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Scoring sentiment for %s", state['stock_symbol'])
    market = state.get("market_intelligence", {}) or {}
    market["sentiment_score"] = 85.0
    return {
        "current_step": "Computing sentiment score",
        "market_intelligence": market
    }

def build_market_intelligence_graph() -> StateGraph:
    """Build the market intelligence sub-graph."""
    builder = StateGraph(InvestmentAnalysisState)
    builder.add_node("fetch_news", fetch_news)
    builder.add_node("sentiment_analysis", sentiment_analysis)
    builder.add_node("macro_context", macro_context)
    builder.add_node("competitor_ranking", competitor_ranking)
    builder.add_node("score_sentiment", score_sentiment)
    
    builder.add_edge(START, "fetch_news")
    builder.add_edge("fetch_news", "sentiment_analysis")
    builder.add_edge("sentiment_analysis", "macro_context")
    builder.add_edge("macro_context", "competitor_ranking")
    builder.add_edge("competitor_ranking", "score_sentiment")
    builder.add_edge("score_sentiment", END)
    
    return builder.compile()
