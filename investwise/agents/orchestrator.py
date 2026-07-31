import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from investwise.agents.state import InvestmentAnalysisState
from investwise.agents.clusters.fundamental import build_fundamental_graph
from investwise.agents.clusters.quant_valuation import build_quant_valuation_graph
from investwise.agents.clusters.market_intelligence import build_market_intelligence_graph
from investwise.agents.clusters.portfolio_guardrails import build_portfolio_guardrails_graph

logger = logging.getLogger('investwise')

def build_orchestrator() -> StateGraph:
    """Build the parent LangGraph that orchestrates all 4 clusters."""
    # 1. Import compiled sub-graphs from clusters
    fundamental_graph = build_fundamental_graph()
    quant_graph = build_quant_valuation_graph()
    market_graph = build_market_intelligence_graph()
    portfolio_graph = build_portfolio_guardrails_graph()
    
    # 2. Create parent StateGraph with InvestmentAnalysisState
    builder = StateGraph(InvestmentAnalysisState)
    
    # 3. Add sub-graphs as nodes:
    builder.add_node("fundamental_cluster", fundamental_graph)
    builder.add_node("quant_cluster", quant_graph)
    builder.add_node("market_intelligence_cluster", market_graph)
    builder.add_node("portfolio_guardrails_cluster", portfolio_graph)
    
    # 4. Define edges:
    # START -> fan-out / parallel
    builder.add_edge(START, "fundamental_cluster")
    builder.add_edge(START, "quant_cluster")
    builder.add_edge(START, "market_intelligence_cluster")
    
    # All three -> fan-in / join
    builder.add_edge("fundamental_cluster", "portfolio_guardrails_cluster")
    builder.add_edge("quant_cluster", "portfolio_guardrails_cluster")
    builder.add_edge("market_intelligence_cluster", "portfolio_guardrails_cluster")
    
    # portfolio_guardrails_cluster -> END
    builder.add_edge("portfolio_guardrails_cluster", END)
    
    # 5. Compile and return
    return builder.compile()

def run_analysis(symbol: str, time_horizon: str, user_id: int, task_id: str) -> dict:
    """Execute the full analysis pipeline."""
    logger.info("Starting analysis for %s", symbol)
    
    # 1. Build orchestrator graph
    orchestrator = build_orchestrator()
    
    # 2. Create initial state
    initial_state: InvestmentAnalysisState = {
        "stock_symbol": symbol,
        "time_horizon": time_horizon,
        "user_id": user_id,
        "task_id": task_id,
        "fundamental_analysis": None,
        "quant_valuation": None,
        "market_intelligence": None,
        "investment_score": None,
        "recommendation": None,
        "confidence": None,
        "shap_explanation": None,
        "portfolio_suggestion": None,
        "nn_prediction": None,
        "errors": [],
        "status": "STARTED",
        "current_step": "Initializing analysis"
    }
    
    # 3. Invoke graph
    try:
        final_state = orchestrator.invoke(initial_state)
    except Exception as e:
        logger.error("Error executing orchestrator graph: %s", str(e))
        initial_state["errors"].append(str(e))
        initial_state["status"] = "FAILED"
        final_state = initial_state
        
    logger.info("Completed analysis for %s", symbol)
    # 4. Return final state as dict
    return final_state
