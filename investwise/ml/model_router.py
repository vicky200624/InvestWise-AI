import logging
from typing import Dict, Any
from investwise.ml.lstm_model import predict_rnn, train_rnn_model
from investwise.ml.fnn_model import predict_fnn, train_fnn_model
from investwise.ml.xgboost_model import predict_investment_score, train_xgboost_scorer
from investwise.models import TrainedModel

logger = logging.getLogger('investwise')

def get_or_train_model(symbol: str, model_type: str) -> str:
    """Check TrainedModel registry; train if no active model exists."""
    try:
        active_models = TrainedModel.objects.filter(symbol=symbol, model_type=model_type, is_active=True)
        if active_models.exists():
            return active_models.latest('created_at').file_path
        
        logger.info(f"No active {model_type} model found for {symbol}, initiating training.")
        if model_type in ['LSTM', 'GRU']:
            result = train_rnn_model(symbol, model_type=model_type)
            return result['model_path']
        elif model_type == 'FNN':
            result = train_fnn_model(symbol)
            return result['model_path']
        else:
            raise ValueError(f"Unsupported model type for auto-training: {model_type}")
    except Exception as e:
        logger.error(f"Error in get_or_train_model for {symbol}: {str(e)}")
        raise

def ensemble_predictions(rnn_pred: Dict[str, Any], fnn_pred: Dict[str, Any], xgb_score: Dict[str, Any],
                         time_horizon: str) -> Dict[str, Any]:
    """Weighted combination of multiple model predictions."""
    try:
        rnn_val = rnn_pred.get('predicted_change_pct', 0)
        fnn_val = fnn_pred.get('prediction', 0)
        xgb_val = xgb_score.get('score', 50)
        
        if time_horizon == 'SHORT_TERM':
            # SHORT: 60% RNN + 20% XGB + 20% FNN
            final_score = (rnn_val * 0.6) + ((xgb_val / 100) * 0.2) + (fnn_val * 0.2)
        else:
            # LONG: 20% RNN + 40% XGB + 40% FNN
            final_score = (rnn_val * 0.2) + ((xgb_val / 100) * 0.4) + (fnn_val * 0.4)
            
        return {
            "ensemble_score": float(final_score),
            "recommendation": "Buy" if final_score > 0.5 else "Sell"
        }
    except Exception as e:
        logger.error(f"Error ensembling predictions: {str(e)}")
        raise

def route_to_model(time_horizon: str, symbol: str) -> Dict[str, Any]:
    """Central routing logic based on user's investment time horizon."""
    try:
        logger.info(f"Routing model request for {symbol} with horizon {time_horizon}")
        
        if time_horizon == 'SHORT_TERM':
            # SHORT_TERM -> LSTM/GRU on price+volume sequences
            get_or_train_model(symbol, 'LSTM')
            prediction = predict_rnn(symbol, model_type='LSTM', horizon_days=5)
            return {
                "model_type": "LSTM",
                "prediction": prediction,
                "confidence": 0.8,
                "features_used": ["Price", "Volume"]
            }
        else:
            # LONG_TERM -> FNN + XGBoost on fundamental+macro features
            get_or_train_model(symbol, 'FNN')
            fnn_prediction = predict_fnn(symbol)
            
            mock_features = {'fundamental_score': 80, 'quant_score': 70, 'sentiment_score': 60, 'time_horizon_encoded': 1}
            xgb_prediction = predict_investment_score(mock_features, model_type='XGBOOST')
            
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
