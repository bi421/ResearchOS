"""
ML-based strategy with BUY and SELL signals.
"""
from typing import List, Any
from dataclasses import dataclass
import pandas as pd
from .features import create_features
from .model import predict

@dataclass
class Signal:
    action: str   # "BUY" or "SELL"
    price: float
    timestamp: Any = None

class MLStrategy:
    def __init__(self, model, scaler, feature_names, threshold=0.55):
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names
        self.threshold = threshold

    def generate_signals(self, prices: List[float]) -> List[Signal]:
        if len(prices) < 50:
            return []

        df = pd.DataFrame({"close": prices})
        df_feat = create_features(df)
        if df_feat.empty:
            return []

        probs, _ = predict(self.model, self.scaler, df_feat, self.feature_names)
        signals = []
        for i, idx in enumerate(df_feat.index):
            if i < len(probs):
                prob = probs[i]
                price = df_feat.loc[idx, 'close']
                if prob > self.threshold:
                    signals.append(Signal("BUY", price))
                elif prob < (1 - self.threshold):
                    signals.append(Signal("SELL", price))
        print(f"📊 Generated {len(signals)} signals (BUY+SELL, threshold={self.threshold})")
        return signals
