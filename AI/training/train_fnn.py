import os
import logging
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import joblib
from typing import Dict, Any

from AI.prediction.model_loader import get_model_dir
from AI.services import fundamentals, macro_data

logger = logging.getLogger('investwise.ai.train_fnn')

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

def prepare_fundamental_features(symbol: str, fmp_api_key: str = "", fred_api_key: str = "") -> pd.DataFrame:
    """Engineer features from financial ratios + macro indicators."""
    try:
        ratios = fundamentals.fetch_ratios(symbol, fmp_api_key=fmp_api_key)
        macro = macro_data.get_macro_snapshot(fred_api_key=fred_api_key)
        
        features = {
            'PE': ratios.get('peRatio', 0) if ratios.get('peRatio') else 0,
            'PB': ratios.get('pbRatio', 0) if ratios.get('pbRatio') else 0,
            'DebtToEquity': ratios.get('debtToEquity', 0) if ratios.get('debtToEquity') else 0,
            'DividendYield': ratios.get('dividendYield', 0) if ratios.get('dividendYield') else 0,
            'GDP_growth': macro.get('GDP', 0),
            'CPI': macro.get('CPI', 0),
            'FedRate': macro.get('FEDFUNDS', 0)
        }
        
        return pd.DataFrame([features])
    except Exception as e:
        logger.error(f"Error preparing fundamental features for {symbol}: {str(e)}")
        raise

def train_fnn_model(symbol: str, epochs: int = 200, model_dir: str = "/home/vicky/Documents/investai/AI/models", fmp_api_key: str = "", fred_api_key: str = "") -> Dict[str, Any]:
    """Train FNN on fundamental features."""
    try:
        logger.info(f"Training FNN for {symbol}...")
        
        features_df = prepare_fundamental_features(symbol, fmp_api_key, fred_api_key)
        # Handle single row scaling by duplicating or dummy data if needed, but for simplicity:
        input_dim = features_df.shape[1]
        
        model = FinancialFNN(input_dim=input_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(pd.concat([features_df, features_df]).values) # Dummy fit
        X_t = torch.FloatTensor(X_scaled[:1])
        y_t = torch.FloatTensor([[1.0]])
        
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = model(X_t)
            loss = criterion(out, y_t)
            loss.backward()
            optimizer.step()
            
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"fnn_{symbol}_{version}.pt"
        scaler_filename = f"fnn_{symbol}_{version}_scaler.joblib"
        
        model_path = os.path.join(get_model_dir(model_dir), model_filename)
        scaler_path = os.path.join(get_model_dir(model_dir), scaler_filename)
        
        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
        
        return {"status": "success", "model_path": model_path, "version": version}
    except Exception as e:
        logger.error(f"Error training FNN for {symbol}: {str(e)}")
        raise
