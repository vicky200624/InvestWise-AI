import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from pypfopt import EfficientFrontier, risk_models, expected_returns, black_litterman
from pypfopt.black_litterman import BlackLittermanModel

from investwise.services import market_data

logger = logging.getLogger('investwise')

def markowitz_optimize(symbols: List[str], risk_free_rate: float = 0.04) -> Dict[str, Any]:
    """Mean-Variance Optimization with Maximum Sharpe Ratio."""
    try:
        logger.info(f"Running Markowitz optimization for {symbols}")
        
        prices_dict = {}
        for sym in symbols:
            df = market_data.fetch_historical_prices(sym)
            prices_dict[sym] = df.set_index('Date')['Close'] if 'Date' in df.columns else df['Close']
            
        prices_df = pd.DataFrame(prices_dict).dropna()
        
        mu = expected_returns.mean_historical_return(prices_df)
        S = risk_models.sample_cov(prices_df)
        
        ef = EfficientFrontier(mu, S)
        weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
        cleaned_weights = ef.clean_weights()
        
        expected_ret, volatility, sharpe = ef.portfolio_performance(verbose=False, risk_free_rate=risk_free_rate)
        
        return {
            "weights": dict(cleaned_weights),
            "expected_return": float(expected_ret),
            "volatility": float(volatility),
            "sharpe": float(sharpe)
        }
    except Exception as e:
        logger.error(f"Error in markowitz optimization: {str(e)}")
        raise

def black_litterman_optimize(symbols: List[str], market_caps: Dict[str, float],
                             views: Dict[str, float], confidences: List[float]) -> Dict[str, Any]:
    """Black-Litterman model with investor views."""
    try:
        logger.info(f"Running Black-Litterman optimization for {symbols}")
        
        prices_dict = {}
        for sym in symbols:
            df = market_data.fetch_historical_prices(sym)
            prices_dict[sym] = df.set_index('Date')['Close'] if 'Date' in df.columns else df['Close']
            
        prices_df = pd.DataFrame(prices_dict).dropna()
        S = risk_models.sample_cov(prices_df)
        
        mcaps = {sym: market_caps.get(sym, 1e9) for sym in symbols}
        
        delta = black_litterman.market_implied_risk_aversion(prices_df)
        market_prior = black_litterman.market_implied_prior_returns(mcaps, delta, S)
        
        bl = BlackLittermanModel(S, pi=market_prior, absolute_views=views, omega="idzorek", view_confidences=confidences)
        ret_bl = bl.bl_returns()
        S_bl = bl.bl_cov()
        
        ef = EfficientFrontier(ret_bl, S_bl)
        weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()
        
        expected_ret, volatility, _ = ef.portfolio_performance(verbose=False)
        
        return {
            "weights": dict(cleaned_weights),
            "expected_return": float(expected_ret),
            "volatility": float(volatility)
        }
    except Exception as e:
        logger.error(f"Error in black_litterman_optimize: {str(e)}")
        raise

def calculate_efficient_frontier(symbols: List[str], n_points: int = 50) -> List[Dict[str, float]]:
    """Generate efficient frontier points for visualization."""
    try:
        prices_dict = {}
        for sym in symbols:
            df = market_data.fetch_historical_prices(sym)
            prices_dict[sym] = df.set_index('Date')['Close'] if 'Date' in df.columns else df['Close']
            
        prices_df = pd.DataFrame(prices_dict).dropna()
        mu = expected_returns.mean_historical_return(prices_df)
        S = risk_models.sample_cov(prices_df)
        
        frontier_points = []
        target_returns = np.linspace(mu.min(), mu.max(), n_points)
        
        for target in target_returns:
            try:
                ef = EfficientFrontier(mu, S)
                ef.efficient_return(target)
                _, vol, sharpe = ef.portfolio_performance()
                frontier_points.append({
                    "return": float(target),
                    "volatility": float(vol),
                    "sharpe": float(sharpe)
                })
            except:
                pass
                
        return frontier_points
    except Exception as e:
        logger.error(f"Error calculating efficient frontier: {str(e)}")
        raise

def suggest_rebalance(current_holdings: Dict[str, float], optimal_weights: Dict[str, float],
                      total_value: float) -> List[Dict[str, Any]]:
    """Generate specific rebalancing trades."""
    try:
        trades = []
        for symbol, current_amount in current_holdings.items():
            target_weight = optimal_weights.get(symbol, 0.0)
            target_amount = total_value * target_weight
            
            diff = target_amount - current_amount
            if abs(diff) > 1.0:
                action = 'BUY' if diff > 0 else 'SELL'
                price = 100.0  # Mocked price
                shares = abs(diff) / price
                
                trades.append({
                    "symbol": symbol,
                    "action": action,
                    "shares": float(shares),
                    "amount": float(abs(diff))
                })
                
        for symbol, weight in optimal_weights.items():
            if symbol not in current_holdings and weight > 0:
                target_amount = total_value * weight
                price = 100.0
                shares = target_amount / price
                trades.append({
                    "symbol": symbol,
                    "action": 'BUY',
                    "shares": float(shares),
                    "amount": float(target_amount)
                })
                
        return trades
    except Exception as e:
        logger.error(f"Error suggesting rebalance: {str(e)}")
        raise
