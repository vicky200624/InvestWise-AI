import os
import logging
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import joblib
from typing import Tuple, Dict, Any

from AI.prediction.model_loader import get_model_dir
from AI.services import market_data

logger = logging.getLogger('investwise.ai.train_lstm')

class FinancialLSTM(nn.Module):
    """LSTM network for sequential price/volume data."""
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 2, output_dim: int = 1, dropout: float = 0.2):
        super(FinancialLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, (hn, cn) = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

class FinancialGRU(nn.Module):
    """GRU variant — faster training, comparable accuracy."""
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 2, output_dim: int = 1, dropout: float = 0.2):
        super(FinancialGRU, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, hn = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out

def prepare_sequences(data: pd.DataFrame, seq_length: int = 60, target_col: str = 'Close') -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
    """Transform time-series into sliding window sequences for RNN input."""
    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        
        feature_cols = [col for col in data.columns if col != 'Date']
        scaled_data = scaler.fit_transform(data[feature_cols])
        
        target_idx = feature_cols.index(target_col) if target_col in feature_cols else 0
        
        X, y = [], []
        for i in range(seq_length, len(scaled_data)):
            X.append(scaled_data[i-seq_length:i])
            y.append(scaled_data[i, target_idx])
            
        X, y = np.array(X), np.array(y)
        
        split = int(0.8 * len(X))
        X_train, y_train = X[:split], y[:split]
        X_test, y_test = X[split:], y[split:]
        
        return X_train, y_train, X_test, y_test, scaler
    except Exception as e:
        logger.error(f"Error preparing sequences: {str(e)}")
        raise

def train_rnn_model(symbol: str, model_type: str = 'LSTM', epochs: int = 100, seq_length: int = 60, model_dir: str = "/home/vicky/Documents/investai/AI/models") -> Dict[str, Any]:
    """Full training pipeline: fetch data -> prepare sequences -> train -> save."""
    try:
        logger.info(f"Training {model_type} for {symbol}...")
        
        df = market_data.fetch_historical_prices(symbol)
        
        X_train, y_train, X_test, y_test, scaler = prepare_sequences(df, seq_length=seq_length)
        
        X_train_t = torch.FloatTensor(X_train)
        y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
        
        dataset = TensorDataset(X_train_t, y_train_t)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        input_dim = X_train.shape[2]
        if model_type == 'LSTM':
            model = FinancialLSTM(input_dim=input_dim)
        else:
            model = FinancialGRU(input_dim=input_dim)
            
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
        
        model.train()
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()
            
            scheduler.step(epoch_loss)
            
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"{model_type.lower()}_{symbol}_{version}.pt"
        scaler_filename = f"{model_type.lower()}_{symbol}_{version}_scaler.joblib"
        
        model_path = os.path.join(get_model_dir(model_dir), model_filename)
        scaler_path = os.path.join(get_model_dir(model_dir), scaler_filename)
        
        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
        
        return {"status": "success", "model_path": model_path, "epochs_trained": epochs, "version": version}
    except Exception as e:
        logger.error(f"Error training RNN model for {symbol}: {str(e)}")
        raise
