import os
import logging
import joblib
import pandas as pd
import numpy as np
import torch
from typing import Dict, Any

from AI.prediction.model_loader import get_latest_model_path, get_model_dir
from AI.training.train_lstm import FinancialLSTM, FinancialGRU, train_rnn_model
from AI.training.train_fnn import FinancialFNN, prepare_fundamental_features, train_fnn_model
from AI.services import market_data

logger = logging.getLogger('investwise.ai.predictor')

def prepare_decision_features(fundamental_score: float, quant_score: float, sentiment_score: float,
                              time_horizon: str, additional_features: dict = None) -> pd.DataFrame:
    """Combine all cluster scores + raw features into XGBoost input."""
    try:
        features = {
            'fundamental_score': fundamental_score,
            'quant_score': quant_score,
            'sentiment_score': sentiment_score,
            'time_horizon_encoded': 1 if time_horizon == 'LONG_TERM' else 0,
        }
        if additional_features:
            features.update(additional_features)
            
        return pd.DataFrame([features])
    except Exception as e:
        logger.error(f"Error preparing decision features: {str(e)}")
        raise

def predict_investment_score(features: Dict[str, Any], model_type: str = 'xgboost', model_dir: str = "/home/vicky/Documents/investai/AI/models") -> Dict[str, Any]:
    """Load active model and predict investment score."""
    try:
        model_path = get_latest_model_path(model_type, model_dir)
        model = joblib.load(model_path)
        features_df = pd.DataFrame([features])
        
        score = model.predict(features_df)[0]
        score = max(0, min(100, score))
        
        recommendation = 'Buy' if score > 70 else ('Hold' if score > 40 else 'Sell')
        
        return {
            "score": float(score),
            "confidence": 0.85,
            "recommendation": recommendation
        }
    except Exception as e:
        logger.error(f"Error predicting investment score: {str(e)}")
        raise

def get_or_train_model(symbol: str, model_type: str, model_dir: str = "/home/vicky/Documents/investai/AI/models", fmp_api_key: str = "", fred_api_key: str = "") -> str:
    """Check registry; train if no active model exists."""
    try:
        try:
            path = get_latest_model_path(f"{model_type}_{symbol}", model_dir)
            return path
        except FileNotFoundError:
            logger.info(f"No active {model_type} model found for {symbol}, initiating training.")
            if model_type in ['LSTM', 'GRU']:
                result = train_rnn_model(symbol, model_type=model_type, model_dir=model_dir)
                return result['model_path']
            elif model_type == 'FNN':
                result = train_fnn_model(symbol, model_dir=model_dir, fmp_api_key=fmp_api_key, fred_api_key=fred_api_key)
                return result['model_path']
            else:
                raise ValueError(f"Unsupported model type for auto-training: {model_type}")
    except Exception as e:
        logger.error(f"Error in get_or_train_model for {symbol}: {str(e)}")
        raise

def predict_rnn(symbol: str, model_type: str = 'LSTM', horizon_days: int = 5, model_dir: str = "/home/vicky/Documents/investai/AI/models") -> Dict[str, Any]:
    """Load trained model and predict future prices."""
    try:
        model_path = get_latest_model_path(f"{model_type}_{symbol}", model_dir)
        version = os.path.basename(model_path).split('_')[-1].replace('.pt', '')
        
        df = market_data.fetch_historical_prices(symbol)
        seq_length = 60
        feature_cols = [col for col in df.columns if col != 'Date']
        
        scaler_filename = f"{model_type.lower()}_{symbol}_{version}_scaler.joblib"
        scaler_path = os.path.join(get_model_dir(model_dir), scaler_filename)
        scaler = joblib.load(scaler_path)
        
        input_dim = len(feature_cols)
        if model_type == 'LSTM':
            model = FinancialLSTM(input_dim=input_dim)
        else:
            model = FinancialGRU(input_dim=input_dim)
            
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        recent_data = df[feature_cols].values[-seq_length:]
        scaled_recent = scaler.transform(recent_data)
        
        curr_seq = torch.FloatTensor(scaled_recent).unsqueeze(0)
        
        predictions = []
        target_idx = feature_cols.index('Close') if 'Close' in feature_cols else 0
        
        with torch.no_grad():
            for _ in range(horizon_days):
                pred = model(curr_seq)
                predictions.append(pred.item())
                
                new_row = curr_seq[0, -1, :].clone()
                new_row[target_idx] = pred.item()
                curr_seq = torch.cat((curr_seq[:, 1:, :], new_row.unsqueeze(0).unsqueeze(0)), dim=1)
                
        dummy_array = np.zeros((len(predictions), input_dim))
        dummy_array[:, target_idx] = predictions
        unscaled_preds = scaler.inverse_transform(dummy_array)[:, target_idx]
        
        current_price = df['Close'].iloc[-1]
        predicted_change_pct = (unscaled_preds[-1] - current_price) / current_price * 100
        
        return {
            "predicted_prices": unscaled_preds.tolist(),
            "current_price": float(current_price),
            "predicted_change_pct": float(predicted_change_pct)
        }
    except Exception as e:
        logger.error(f"Error predicting with RNN for {symbol}: {str(e)}")
        raise

def predict_fnn(symbol: str, model_dir: str = "/home/vicky/Documents/investai/AI/models", fmp_api_key: str = "", fred_api_key: str = "") -> Dict[str, Any]:
    """Predict using trained FNN model."""
    try:
        model_path = get_latest_model_path(f"fnn_{symbol}", model_dir)
        version = os.path.basename(model_path).split('_')[-1].replace('.pt', '')
        
        features_df = prepare_fundamental_features(symbol, fmp_api_key, fred_api_key)
        input_dim = features_df.shape[1]
        
        scaler_path = os.path.join(get_model_dir(model_dir), f"fnn_{symbol}_{version}_scaler.joblib")
        scaler = joblib.load(scaler_path)
        
        X_scaled = scaler.transform(features_df.values)
        X_t = torch.FloatTensor(X_scaled)
        
        model = FinancialFNN(input_dim=input_dim)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        with torch.no_grad():
            pred = model(X_t).item()
            
        return {
            "prediction": float(pred),
            "features_used": features_df.columns.tolist()
        }
    except Exception as e:
        logger.error(f"Error predicting with FNN for {symbol}: {str(e)}")
        raise

def ensemble_predictions(rnn_pred: Dict[str, Any], fnn_pred: Dict[str, Any], xgb_score: Dict[str, Any],
                         time_horizon: str) -> Dict[str, Any]:
    """Weighted combination of multiple model predictions."""
    try:
        rnn_val = rnn_pred.get('predicted_change_pct', 0)
        fnn_val = fnn_pred.get('prediction', 0)
        xgb_val = xgb_score.get('score', 50)
        
        if time_horizon == 'SHORT_TERM':
            final_score = (rnn_val * 0.6) + ((xgb_val / 100) * 0.2) + (fnn_val * 0.2)
        else:
            final_score = (rnn_val * 0.2) + ((xgb_val / 100) * 0.4) + (fnn_val * 0.4)
            
        return {
            "ensemble_score": float(final_score),
            "recommendation": "Buy" if final_score > 0.5 else "Sell"
        }
    except Exception as e:
        logger.error(f"Error ensembling predictions: {str(e)}")
        raise

def route_to_model(time_horizon: str, symbol: str, model_dir: str = "/home/vicky/Documents/investai/AI/models", fmp_api_key: str = "", fred_api_key: str = "") -> Dict[str, Any]:
    """Central routing logic based on user's investment time horizon."""
    try:
        logger.info(f"Routing model request for {symbol} with horizon {time_horizon}")
        
        if time_horizon == 'SHORT_TERM':
            get_or_train_model(symbol, 'LSTM', model_dir=model_dir)
            prediction = predict_rnn(symbol, model_type='LSTM', horizon_days=5, model_dir=model_dir)
            return {
                "model_type": "LSTM",
                "prediction": prediction,
                "confidence": 0.8,
                "features_used": ["Price", "Volume"]
            }
        else:
            get_or_train_model(symbol, 'FNN', model_dir=model_dir, fmp_api_key=fmp_api_key, fred_api_key=fred_api_key)
            fnn_prediction = predict_fnn(symbol, model_dir=model_dir, fmp_api_key=fmp_api_key, fred_api_key=fred_api_key)
            
            mock_features = {'fundamental_score': 80, 'quant_score': 70, 'sentiment_score': 60, 'time_horizon_encoded': 1}
            try:
                xgb_prediction = predict_investment_score(mock_features, model_type='xgboost', model_dir=model_dir)
            except Exception:
                xgb_prediction = {"score": 50, "recommendation": "Hold"}
            
            return {
                "model_type": "FNN_XGBOOST",
                "prediction": fnn_prediction,
                "xgb_score": xgb_prediction,
                "confidence": 0.85,
                "features_used": fnn_prediction.get('features_used', [])
            }
    except Exception as e:
        logger.error(f"Error routing model for {symbol}: {str(e)}")
        raise
