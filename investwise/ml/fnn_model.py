import os
import logging
from typing import Dict, Any
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from django.conf import settings
from django.utils import timezone
import joblib

from investwise.models import TrainedModel
from investwise.services import fundamentals, macro_data

logger = logging.getLogger('investwise')

class FinancialFNN(nn.Module):
    """FNN for fundamental + macro feature-based prediction."""
    def __init__(self, input_dim: int, output_dim: int = 1):
        super(FinancialFNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(0.2),
            
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.Dropout(0.2),
            
            nn.Linear(64, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for FNN."""
        return self.net(x)

def prepare_fundamental_features(symbol: str) -> pd.DataFrame:
    """Engineer features from financial ratios + macro indicators."""
    try:
        ratios = fundamentals.get_ratios(symbol)
        macro = macro_data.get_current_indicators()
        
        features = {
            'PE': ratios.get('pe_ratio', 0),
            'PB': ratios.get('pb_ratio', 0),
            'ROE': ratios.get('roe', 0),
            'DebtToEquity': ratios.get('debt_to_equity', 0),
            'CurrentRatio': ratios.get('current_ratio', 0),
            'RevenueGrowth': ratios.get('revenue_growth', 0),
            'EarningsGrowth': ratios.get('earnings_growth', 0),
            'DividendYield': ratios.get('dividend_yield', 0),
            'GDP_growth': macro.get('gdp_growth', 0),
            'CPI': macro.get('cpi', 0),
            'FedRate': macro.get('fed_rate', 0)
        }
        
        return pd.DataFrame([features])
    except Exception as e:
        logger.error(f"Error preparing fundamental features for {symbol}: {str(e)}")
        raise

def train_fnn_model(symbol: str, epochs: int = 200) -> Dict[str, Any]:
    """Train FNN on fundamental features."""
    try:
        logger.info(f"Training FNN for {symbol}...")
        
        features_df = prepare_fundamental_features(symbol)
        input_dim = features_df.shape[1]
        
        model = FinancialFNN(input_dim=input_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(features_df.values)
        X_t = torch.FloatTensor(X_scaled)
        y_t = torch.FloatTensor([[1.0]])
        
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = model(X_t)
            loss = criterion(out, y_t)
            loss.backward()
            optimizer.step()
            
        version = timezone.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"fnn_{symbol}_{version}.pt"
        scaler_filename = f"fnn_{symbol}_{version}_scaler.joblib"
        
        model_path = os.path.join(settings.AI_MODEL_DIR, model_filename)
        scaler_path = os.path.join(settings.AI_MODEL_DIR, scaler_filename)
        
        os.makedirs(settings.AI_MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
        
        TrainedModel.objects.create(
            symbol=symbol,
            model_type='FNN',
            version=version,
            file_path=model_path,
            is_active=True
        )
        
        return {"status": "success", "model_path": model_path}
    except Exception as e:
        logger.error(f"Error training FNN for {symbol}: {str(e)}")
        raise

def predict_fnn(symbol: str) -> Dict[str, Any]:
    """Predict using trained FNN model."""
    try:
        active_model = TrainedModel.objects.filter(symbol=symbol, model_type='FNN', is_active=True).latest('created_at')
        
        features_df = prepare_fundamental_features(symbol)
        input_dim = features_df.shape[1]
        
        scaler_path = os.path.join(settings.AI_MODEL_DIR, f"fnn_{symbol}_{active_model.version}_scaler.joblib")
        scaler = joblib.load(scaler_path)
        
        X_scaled = scaler.transform(features_df.values)
        X_t = torch.FloatTensor(X_scaled)
        
        model = FinancialFNN(input_dim=input_dim)
        model.load_state_dict(torch.load(active_model.file_path))
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
