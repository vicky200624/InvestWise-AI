"""
LangGraph state definitions for InvestWise AI 3.0 Platform.
Enforces typed state flowing through all 10 orchestrator nodes and 4 specialized agent clusters.
Zero Django dependencies.
"""

from typing import TypedDict, Dict, Any, List, Optional


class AgentState(TypedDict, total=False):
    """
    Comprehensive state flowing through the 10-node LangGraph pipeline.
    """
    # 14 Core state variables required by Part 2 spec
    user_profile: Dict[str, Any]
    investment_horizon: str           # e.g. 'SHORT', 'LONG', '5Y'
    risk_tolerance: str               # e.g. 'LOW', 'MODERATE', 'HIGH'
    portfolio: Dict[str, Any]
    market_condition: str             # e.g. 'BULLISH', 'BEARISH', 'NEUTRAL'
    company: Dict[str, Any]
    chat_history: List[Dict[str, Any]]
    rag_context: List[Dict[str, Any]]
    news_summary: List[Dict[str, Any]]
    financial_metrics: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    macro_indicators: Dict[str, Any]
    intermediate_conclusions: Dict[str, Any]
    confidence_scores: Dict[str, float]

    # Input and progress identifiers
    stock_symbol: str
    time_horizon: str
    user_id: Optional[int]
    task_id: Optional[str]
    current_step: str
    status: str
    errors: List[str]

    # Cluster Outputs
    research_intelligence: Dict[str, Any]
    financial_intelligence: Dict[str, Any]
    market_intelligence: Dict[str, Any]
    decision_intelligence: Dict[str, Any]
    portfolio_optimization: Dict[str, Any]

    # Legacy alias fields for backward compatibility
    fundamental_analysis: Dict[str, Any]
    quant_valuation: Dict[str, Any]
    nn_prediction: Dict[str, Any]
    portfolio_suggestion: Dict[str, Any]

    # Final JSON output fields required by Part 2 spec
    recommendation: str
    investment_score: float
    confidence: float
    expected_cagr: float
    risk_score: float
    bull_case: str
    base_case: str
    bear_case: str
    business_summary: str
    financial_summary: str
    technical_summary: str
    macro_summary: str
    portfolio_impact: Dict[str, Any]
    shap_explanation: Dict[str, Any]
    sources: List[str]
    timestamp: str
    model_version: str


# Backward-compatibility alias
InvestmentAnalysisState = AgentState
