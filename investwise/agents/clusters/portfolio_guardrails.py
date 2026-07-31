import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from investwise.agents.state import InvestmentAnalysisState

logger = logging.getLogger('investwise')

def fuse_features(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Fusing features for %s", state['stock_symbol'])
    return {
        "current_step": "Fusing cluster features"
    }

def xgboost_score(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Predicting xgboost score for %s", state['stock_symbol'])
    return {
        "current_step": "Predicting investment score",
        "investment_score": 75.5
    }

def generate_explanation(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Generating SHAP explanation for %s", state['stock_symbol'])
    return {
        "current_step": "Generating SHAP explanation",
        "shap_explanation": {"features": ["ROE", "RSI", "Sentiment"]}
    }

def portfolio_optimize(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Optimizing portfolio for user %s", state['user_id'])
    return {
        "current_step": "Running portfolio optimization",
        "portfolio_suggestion": {"allocations": {state['stock_symbol']: 0.1}}
    }

def apply_guardrails(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Applying guardrails for %s", state['stock_symbol'])
    return {
        "current_step": "Applying risk guardrails"
    }

def generate_recommendation(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Generating recommendation for %s", state['stock_symbol'])
    score = state.get("investment_score", 50.0)
    
    if score < 20:
        rec = "STRONG_SELL"
    elif score < 40:
        rec = "SELL"
    elif score < 60:
        rec = "HOLD"
    elif score < 80:
        rec = "BUY"
    else:
        rec = "STRONG_BUY"
        
    return {
        "current_step": "Generating final recommendation",
        "recommendation": rec,
        "confidence": 0.85,
        "status": "COMPLETED"
    }

def build_portfolio_guardrails_graph() -> StateGraph:
    """Build the portfolio guardrails sub-graph."""
    builder = StateGraph(InvestmentAnalysisState)
    builder.add_node("fuse_features", fuse_features)
    builder.add_node("xgboost_score", xgboost_score)
    builder.add_node("generate_explanation", generate_explanation)
    builder.add_node("portfolio_optimize", portfolio_optimize)
    builder.add_node("apply_guardrails", apply_guardrails)
    builder.add_node("generate_recommendation", generate_recommendation)
    
    builder.add_edge(START, "fuse_features")
    builder.add_edge("fuse_features", "xgboost_score")
    builder.add_edge("xgboost_score", "generate_explanation")
    builder.add_edge("generate_explanation", "portfolio_optimize")
    builder.add_edge("portfolio_optimize", "apply_guardrails")
    builder.add_edge("apply_guardrails", "generate_recommendation")
    builder.add_edge("generate_recommendation", END)
    
    return builder.compile()
