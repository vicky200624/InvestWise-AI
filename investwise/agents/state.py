from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class InvestmentAnalysisState(TypedDict):
    """Shared state flowing through all 4 analysis clusters."""
    # Input (set by orchestrator)
    stock_symbol: str
    time_horizon: str           # 'SHORT' or 'LONG'
    user_id: int
    task_id: str                # AgentTask UUID for progress tracking
    
    # Cluster outputs (populated by each sub-graph)
    fundamental_analysis: dict | None
    quant_valuation: dict | None
    market_intelligence: dict | None
    
    # Decision outputs (populated by Portfolio cluster)
    investment_score: float | None
    recommendation: str | None
    confidence: float | None
    shap_explanation: dict | None
    portfolio_suggestion: dict | None
    nn_prediction: dict | None
    
    # Metadata
    errors: list[str]
    status: str
    current_step: str
