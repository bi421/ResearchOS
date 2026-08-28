"""Minimal smoke test for ML pipeline."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from researchos.engines.quant.machine_learning.deep_models import SequenceModel
from researchos.engines.quant.machine_learning.explainability import monte_carlo_dropout
from researchos.engines.quant.machine_learning.purged_validation import expanding_window_folds
from researchos.engines.quant.machine_learning.risk import combined_position_sizing

# Minimal data test
print("Creating minimal test data...")
np.random.seed(42)
n = 1000
X = np.random.randn(n, 10, 5).astype(np.float32)
y = np.random.randn(n).astype(np.float32)

print("Testing LSTM model...")
model = SequenceModel("lstm", input_dim=5, seq_len=10, hidden_dim=16, rng_seed=42)
pred = model.forward(X[:10], training=False)
print(f"  Output shape: {pred.shape}")

print("Testing MC dropout...")
mc = monte_carlo_dropout(model, X[:10], n_samples=10)
print(f"  Mean uncertainty: {np.mean(mc['std']):.6f}")

print("Testing walk-forward folds...")
folds = expanding_window_folds(n, initial_train_size=500, test_size=200, step_size=200)
print(f"  Number of folds: {len(folds)}")

print("Testing position sizing...")
result = combined_position_sizing(prediction=0.01, confidence=0.8, uncertainty=0.1, win_prob=0.55, avg_win=0.02, avg_loss=0.01, current_volatility=0.15)
print(f"  Position size: {result.position_size:.4f}")

print("\nAll components working correctly!")
