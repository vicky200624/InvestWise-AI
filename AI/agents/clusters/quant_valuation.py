import logging
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from AI.agents.state import InvestmentAnalysisState
from AI.services import market_data
from AI.prediction.predictor import predict_rnn

logger = logging.getLogger('investwise.ai.quant_valuation')

def calculate_dcf(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Calculating DCF for %s", state['stock_symbol'])
    quant = state.get("quant_valuation", {}) or {}
    
    # Mocked real calculation. In real app, this uses fundamentals.
    quant["dcf_value"] = 150.0
    quant["current_price"] = 120.0
    quant["upside"] = (150.0 - 120.0) / 120.0
    
    return {
        "current_step": "Calculating DCF",
        "quant_valuation": quant
    }

def technical_analysis(state: InvestmentAnalysisState) -> Dict[str, Any]:
    symbol = state['stock_symbol']
    logger.info("Technical analysis for %s", symbol)
    quant = state.get("quant_valuation", {}) or {}
    
    try:
        indicators = market_data.fetch_technical_indicators(symbol)
        quant["technical_indicators"] = indicators
        return {
            "current_step": "Technical analysis",
            "quant_valuation": quant
        }
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return {
            "current_step": "Technical analysis failed",
            "quant_valuation": quant,
            "errors": state.get("errors", []) + [str(e)]
        }

def neural_prediction(state: InvestmentAnalysisState) -> Dict[str, Any]:
    symbol = state['stock_symbol']
    logger.info("Neural prediction for %s", symbol)
    quant = state.get("quant_valuation", {}) or {}
    
    try:
        # Load from models dir. Assumes model exists or catches error.
        prediction = predict_rnn(symbol, model_type='LSTM', horizon_days=5)
        quant["nn_prediction"] = prediction
        state["nn_prediction"] = prediction # Also store in root state
        return {
            "current_step": "Neural prediction",
            "quant_valuation": quant,
            "nn_prediction": prediction
        }
    except Exception as e:
        logger.error(f"Error in neural prediction: {e}")
        quant["nn_prediction"] = None
        return {
            "current_step": "Neural prediction failed",
            "quant_valuation": quant,
            "errors": state.get("errors", []) + [str(e)]
        }

def score_quant(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Scoring quant for %s", state['stock_symbol'])
    quant = state.get("quant_valuation", {}) or {}
    
    # Calculate score based on DCF upside, RSI, MACD, and NN predicted change
    upside = quant.get("upside", 0)
    nn_change = quant.get("nn_prediction", {}).get("predicted_change_pct", 0) if quant.get("nn_prediction") else 0
    
    score = 50 + (upside * 100) + (nn_change * 5)
    quant["quant_score"] = max(0, min(100, score))
    
    return {
        "current_step": "Scoring quant",
        "quant_valuation": quant
    }

def build_quant_valuation_graph() -> StateGraph:
    """Build the quant valuation sub-graph."""
    builder = StateGraph(InvestmentAnalysisState)
    builder.add_node("calculate_dcf", calculate_dcf)
    builder.add_node("technical_analysis", technical_analysis)
    builder.add_node("neural_prediction", neural_prediction)
    builder.add_node("score_quant", score_quant)
    
    builder.add_edge(START, "calculate_dcf")
    builder.add_edge("calculate_dcf", "technical_analysis")
    builder.add_edge("technical_analysis", "neural_prediction")
    builder.add_edge("neural_prediction", "score_quant")
    builder.add_edge("score_quant", END)
    
    return builder.compile()
