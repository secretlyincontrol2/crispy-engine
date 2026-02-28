"""
LSTM Model Utilities
====================
Handles loading the PyTorch LSTM model and scaler, preprocessing sales data
into the required (1, 30, 5) tensor, running inference, and inverse-scaling
the output back to real demand units.

Model contract:
  - Input shape:  (batch, 30, 5)   — 30 days × 5 features
  - Features:     [sales, price, promo, weekday, month]
  - Output:       single float (scaled 0–1), inverse-transform to get units
"""

import math
import logging
from datetime import timedelta

import numpy as np
import torch
import torch.nn as nn
import joblib
from django.conf import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  LSTM Architecture  (must match training)
# ─────────────────────────────────────────────

class DemandLSTM(nn.Module):
    """PyTorch LSTM for demand forecasting."""

    def __init__(self, input_size=5, hidden_size=64, num_layers=2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])  # take last time-step
        return out


# ─────────────────────────────────────────────
#  Singleton loader  (loaded once at first use)
# ─────────────────────────────────────────────

_model = None
_scaler = None


def _load_model():
    """Load model weights and scaler from disk (lazy singleton)."""
    global _model, _scaler

    model_path = settings.AI_MODEL_PATH
    scaler_path = settings.AI_SCALER_PATH

    # Load scaler
    _scaler = joblib.load(scaler_path)
    logger.info("Scaler loaded from %s", scaler_path)

    # Load model
    _model = DemandLSTM(
        input_size=settings.LSTM_INPUT_SIZE,
        hidden_size=settings.LSTM_HIDDEN_SIZE,
        num_layers=settings.LSTM_NUM_LAYERS,
    )
    _model.load_state_dict(torch.load(model_path, map_location='cpu'))
    _model.eval()
    logger.info("LSTM model loaded from %s", model_path)


def get_model():
    if _model is None:
        _load_model()
    return _model


def get_scaler():
    if _scaler is None:
        _load_model()
    return _scaler


# ─────────────────────────────────────────────
#  Data preprocessing
# ─────────────────────────────────────────────

def build_feature_matrix(daily_sales, product_price, promo_flags=None):
    """
    Build a (30, 5) feature matrix from the last 30 days of sales.

    Parameters
    ----------
    daily_sales : list[dict]
        Each dict has keys: 'date' (datetime.date), 'total_qty' (int).
        Must be sorted ascending by date. Gaps will be filled with 0.
    product_price : float
        Current product price (used for the price feature).
    promo_flags : dict[str, int] | None
        Optional mapping of date-string → 0/1 promo flag. Defaults to 0.

    Returns
    -------
    np.ndarray of shape (30, 5)
    """
    seq_len = settings.LSTM_SEQUENCE_LENGTH  # 30

    if not daily_sales:
        # No sales history — return zeros
        return np.zeros((seq_len, 5), dtype=np.float32)

    # Build a date → qty lookup
    from datetime import date as dt_date
    sales_lookup = {row['date']: row['total_qty'] for row in daily_sales}

    # Determine the 30-day window ending on the latest date
    latest_date = max(sales_lookup.keys())
    start_date = latest_date - timedelta(days=seq_len - 1)

    features = []
    for i in range(seq_len):
        d = start_date + timedelta(days=i)
        sales = sales_lookup.get(d, 0)
        price = float(product_price)
        promo = (promo_flags or {}).get(str(d), 0)
        weekday = d.weekday()     # 0=Monday … 6=Sunday
        month = d.month           # 1–12
        features.append([sales, price, promo, weekday, month])

    return np.array(features, dtype=np.float32)


# ─────────────────────────────────────────────
#  Prediction pipeline
# ─────────────────────────────────────────────

def predict_demand(daily_sales, product_price, promo_flags=None):
    """
    Full prediction pipeline:
      1. Build feature matrix  (30, 5)
      2. Scale with the training scaler  (.transform only — never .fit)
      3. Convert to tensor  (1, 30, 5)
      4. Run inference in eval / no_grad mode
      5. Inverse-scale and round up

    Returns
    -------
    int — predicted demand in whole units
    """
    model = get_model()
    scaler = get_scaler()

    # Step 1 — features
    features = build_feature_matrix(daily_sales, product_price, promo_flags)

    # Step 2 — scale (transform only, DO NOT fit)
    features_scaled = scaler.transform(features)

    # Step 3 — tensor
    tensor = torch.FloatTensor(features_scaled).unsqueeze(0)  # (1, 30, 5)

    # Step 4 — inference
    with torch.no_grad():
        raw_output = model(tensor)  # shape (1, 1)

    raw_value = raw_output.item()

    # Step 5 — inverse scale
    # The model outputs a single scaled value (the sales column).
    # We need to inverse-transform using only the first column of the scaler.
    dummy = np.zeros((1, 5), dtype=np.float32)
    dummy[0, 0] = raw_value
    inversed = scaler.inverse_transform(dummy)
    predicted_units = inversed[0, 0]

    # Round up — can't sell fractional units
    return math.ceil(max(predicted_units, 0))
