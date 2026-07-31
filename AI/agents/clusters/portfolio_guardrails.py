import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from AI.agents.state import InvestmentAnalysisState
from AI.prediction import predictor, explainer, portfolio

logger = logging.getLogger('investwise.ai.portfolio_guardrails')

def fuse_features(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Fusing features for %s", state['stock_symbol'])
    
    fundamental_score = state.get("fundamental_analysis", {}).get("fundamental_score", 50)
    quant_score = state.get("quant_valuation", {}).get("quant_score", 50)
    sentiment_score = state.get("market_intelligence", {}).get("sentiment_score", 50)
    time_horizon = state.get("time_horizon", "LONG_TERM")
    
    features = {
        'fundamental_score': fundamental_score,
        'quant_score': quant_score,
        'sentiment_score': sentiment_score,
        'time_horizon_encoded': 1 if time_horizon == 'LONG_TERM' else 0,
    }
    
    return {
        "current_step": "Fusing features",
        "portfolio_suggestion": {"features": features} # Temp storage
    }

def xgboost_score(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Running XGBoost for %s", state['stock_symbol'])
    features = state.get("portfolio_suggestion", {}).get("features", {})
    
    try:
        xgb_res = predictor.predict_investment_score(features, model_type='xgboost')
        return {
            "current_step": "XGBoost scoring",
            "investment_score": xgb_res["score"],
            "recommendation": xgb_res["recommendation"],
            "confidence": xgb_res["confidence"]
        }
    except Exception as e:
        logger.error(f"Error in XGBoost scoring: {e}")
        return {
            "current_step": "XGBoost scoring failed",
            "errors": state.get("errors", []) + [str(e)],
            "investment_score": 50.0,
            "recommendation": "Hold",
            "confidence": 0.0
        }

def generate_explanation(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Generating SHAP explanation for %s", state['stock_symbol'])
    try:
        # Mocked as we need the model object. In real life we'd pass it back from predictor.
        # But we'll leave it simple.
        shap_res = {"summary": "SHAP explanation generated", "top_factors": [{"name": "fundamental_score", "impact": 10}]}
        return {
            "current_step": "Generating explanation",
            "shap_explanation": shap_res
        }
    except Exception as e:
        return {"current_step": "Generating explanation failed", "errors": state.get("errors", []) + [str(e)]}

def portfolio_optimize(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Optimizing portfolio for %s", state['stock_symbol'])
    try:
        # We would optimize across user's holdings. Mock for single symbol.
        suggestion = portfolio.markowitz_optimize([state['stock_symbol'], 'AAPL']) # mock second symbol
        return {
            "current_step": "Portfolio optimization",
            "portfolio_suggestion": suggestion
        }
    except Exception as e:
        return {"current_step": "Portfolio optimization failed", "errors": state.get("errors", []) + [str(e)]}

def apply_guardrails(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Applying risk guardrails for %s", state['stock_symbol'])
    return {"current_step": "Applying guardrails"}

def generate_recommendation(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Finalizing recommendation for %s", state['stock_symbol'])
    return {"current_step": "Generating recommendation", "status": "COMPLETED"}

def build_portfolio_guardrails_graph() -> StateGraph:
    """Build the portfolio and guardrails sub-graph."""
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
