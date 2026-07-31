import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from investwise.agents.state import InvestmentAnalysisState
from django.conf import settings

logger = logging.getLogger('investwise')

def calculate_dcf(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Calculating DCF for %s", state['stock_symbol'])
    return {
        "current_step": "Calculating DCF intrinsic value",
        "quant_valuation": {"intrinsic_value": 150.0, "margin_of_safety_pct": 20.0}
    }

def technical_analysis(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Running technical analysis for %s", state['stock_symbol'])
    quant = state.get("quant_valuation", {}) or {}
    quant["technical_signals"] = {"rsi": 45, "macd": "bullish"}
    return {
        "current_step": "Analyzing technical indicators",
        "quant_valuation": quant
    }

def neural_prediction(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Running neural prediction for %s (%s)", state['stock_symbol'], state['time_horizon'])
    quant = state.get("quant_valuation", {}) or {}
    quant["prediction_direction"] = "up"
    return {
        "current_step": "Generating neural network predictions",
        "quant_valuation": quant,
        "nn_prediction": {"direction": "up", "confidence": 0.8}
    }

def score_quant(state: InvestmentAnalysisState) -> dict[str, Any]:
    logger.info("Scoring quant for %s", state['stock_symbol'])
    quant = state.get("quant_valuation", {}) or {}
    quant["quant_score"] = 80.0
    return {
        "current_step": "Computing quant score",
        "quant_valuation": quant
    }

def build_quant_valuation_graph() -> StateGraph:
    """Build the quant and valuation sub-graph."""
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
