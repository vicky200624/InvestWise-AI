import os
import logging
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from django.conf import settings
from django.utils import timezone
import joblib

from investwise.models import TrainedModel
from investwise.services import market_data

logger = logging.getLogger('investwise')

class FinancialLSTM(nn.Module):
    """LSTM network for sequential price/volume data."""
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 2, output_dim: int = 1, dropout: float = 0.2):
        super(FinancialLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for LSTM.
        x: (batch, seq_len, input_dim)
        """
        out, (hn, cn) = self.lstm(x)
        # Return last hidden state through FC layer
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
        """
        Forward pass for GRU.
        x: (batch, seq_len, input_dim)
        """
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

def train_rnn_model(symbol: str, model_type: str = 'LSTM', epochs: int = 100, seq_length: int = 60) -> Dict[str, Any]:
    """Full training pipeline: fetch data -> prepare sequences -> train -> save -> register."""
    try:
        logger.info(f"Training {model_type} for {symbol}...")
        
        # 1. Fetch historical prices via services.market_data
        df = market_data.fetch_historical_prices(symbol)
        
        # 2. Prepare sequences
        X_train, y_train, X_test, y_test, scaler = prepare_sequences(df, seq_length=seq_length)
        
        X_train_t = torch.FloatTensor(X_train)
        y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
        
        dataset = TensorDataset(X_train_t, y_train_t)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # 3. Train with early stopping, gradient clipping, ReduceLROnPlateau
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
            
        # 4. Save model to settings.AI_MODEL_DIR
        version = timezone.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"{model_type.lower()}_{symbol}_{version}.pt"
        scaler_filename = f"{model_type.lower()}_{symbol}_{version}_scaler.joblib"
        
        model_path = os.path.join(settings.AI_MODEL_DIR, model_filename)
        scaler_path = os.path.join(settings.AI_MODEL_DIR, scaler_filename)
        
        os.makedirs(settings.AI_MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
        
        # 5. Register in TrainedModel Django model
        TrainedModel.objects.create(
            symbol=symbol,
            model_type=model_type,
            version=version,
            file_path=model_path,
            is_active=True
        )
        
        return {"status": "success", "model_path": model_path, "epochs_trained": epochs}
    except Exception as e:
        logger.error(f"Error training RNN model for {symbol}: {str(e)}")
        raise

def predict_rnn(symbol: str, model_type: str = 'LSTM', horizon_days: int = 5) -> Dict[str, Any]:
    """Load trained model and predict future prices."""
    try:
        active_model_record = TrainedModel.objects.filter(symbol=symbol, model_type=model_type, is_active=True).latest('created_at')
        
        df = market_data.fetch_historical_prices(symbol)
        seq_length = 60
        feature_cols = [col for col in df.columns if col != 'Date']
        
        scaler_filename = f"{model_type.lower()}_{symbol}_{active_model_record.version}_scaler.joblib"
        scaler_path = os.path.join(settings.AI_MODEL_DIR, scaler_filename)
        scaler = joblib.load(scaler_path)
        
        input_dim = len(feature_cols)
        if model_type == 'LSTM':
            model = FinancialLSTM(input_dim=input_dim)
        else:
            model = FinancialGRU(input_dim=input_dim)
            
        model.load_state_dict(torch.load(active_model_record.file_path))
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
