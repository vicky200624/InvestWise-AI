import logging
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from AI.agents.state import InvestmentAnalysisState
from AI.services import fundamentals
from AI.services import rag_engine

logger = logging.getLogger('investwise.ai.fundamental')

def fetch_financials(state: InvestmentAnalysisState) -> Dict[str, Any]:
    symbol = state['stock_symbol']
    logger.info("Fetching financials for %s", symbol)
    try:
        fmp_key = os.environ.get("FMP_API_KEY", "")
        ratios = fundamentals.fetch_ratios(symbol, fmp_api_key)
        profile = fundamentals.fetch_company_profile(symbol, fmp_api_key)
        
        financials = {
            "ratios": ratios,
            "profile": profile
        }
        return {
            "current_step": "Fetching financial data",
            "fundamental_analysis": {"financials": financials}
        }
    except Exception as e:
        logger.error(f"Error fetching financials: {e}")
        return {
            "current_step": "Fetching financial data failed",
            "errors": state.get("errors", []) + [str(e)]
        }

def rag_corporate_docs(state: InvestmentAnalysisState) -> Dict[str, Any]:
    symbol = state['stock_symbol']
    logger.info("Running RAG for corporate docs for %s", symbol)
    analysis = state.get("fundamental_analysis", {}) or {}
    
    try:
        # Assumes sec documents for symbol were previously ingested into a collection named f"sec_{symbol}"
        results = rag_engine.query_documents(f"What are the competitive advantages and risks for {symbol}?", f"sec_{symbol}", n_results=3)
        context = " ".join([r['document'] for r in results]) if results else "No SEC filings found."
        analysis["rag_docs"] = context
        return {
            "current_step": "Analyzing SEC filings via RAG",
            "fundamental_analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error in RAG: {e}")
        analysis["rag_docs"] = "Error retrieving SEC docs."
        return {
            "current_step": "Analyzing SEC filings via RAG",
            "fundamental_analysis": analysis,
            "errors": state.get("errors", []) + [str(e)]
        }

def evaluate_business_quality(state: InvestmentAnalysisState) -> Dict[str, Any]:
    symbol = state['stock_symbol']
    logger.info("Evaluating business quality for %s", symbol)
    analysis = state.get("fundamental_analysis", {}) or {}
    
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
            prompt = f"Evaluate the business quality of {symbol} based on these notes: {analysis.get('rag_docs', '')}. Return a score from 0-100 and a 1-sentence summary."
            response = llm.invoke(prompt)
            # Naive parsing
            content = response.content
            analysis["business_quality"] = content
            analysis["llm_score"] = 75.0 # Extracted from LLM in a real scenario
        else:
            analysis["business_quality"] = "No API key provided."
            analysis["llm_score"] = 50.0
    except Exception as e:
        logger.error("Error evaluating business quality: %s", str(e))
        analysis["business_quality"] = "Evaluation failed."
        analysis["llm_score"] = 50.0
        return {"current_step": "Evaluating business quality", "fundamental_analysis": analysis, "errors": state.get("errors", []) + [str(e)]}
        
    return {
        "current_step": "Evaluating business quality",
        "fundamental_analysis": analysis
    }

def score_fundamentals(state: InvestmentAnalysisState) -> Dict[str, Any]:
    logger.info("Scoring fundamentals for %s", state['stock_symbol'])
    analysis = state.get("fundamental_analysis", {}) or {}
    
    try:
        ratios = analysis.get("financials", {}).get("ratios", {})
        roe = float(ratios.get('roe', 0) or 0)
        debt_eq = float(ratios.get('debtToEquity', 0) or 0)
        
        # very naive scoring rule based on roe and debt_eq
        base_score = 50
        base_score += min(30, roe * 100) # up to 30 pts for ROE
        base_score -= min(20, debt_eq * 10) # penalize high debt
        
        llm_score = analysis.get("llm_score", 50)
        
        final_score = (base_score * 0.7) + (llm_score * 0.3)
        analysis["fundamental_score"] = max(0, min(100, final_score))
        
        return {
            "current_step": "Scoring fundamentals",
            "fundamental_analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error scoring fundamentals: {e}")
        analysis["fundamental_score"] = 50.0
        return {
            "current_step": "Scoring fundamentals failed",
            "fundamental_analysis": analysis,
            "errors": state.get("errors", []) + [str(e)]
        }

def build_fundamental_graph() -> StateGraph:
    """Build the fundamental analysis sub-graph."""
    builder = StateGraph(InvestmentAnalysisState)
    builder.add_node("fetch_financials", fetch_financials)
    builder.add_node("rag_corporate_docs", rag_corporate_docs)
    builder.add_node("evaluate_business_quality", evaluate_business_quality)
    builder.add_node("score_fundamentals", score_fundamentals)
    
    builder.add_edge(START, "fetch_financials")
    builder.add_edge("fetch_financials", "rag_corporate_docs")
    builder.add_edge("rag_corporate_docs", "evaluate_business_quality")
    builder.add_edge("evaluate_business_quality", "score_fundamentals")
    builder.add_edge("score_fundamentals", END)
    
    return builder.compile()
