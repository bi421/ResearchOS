import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential


class LSTMPredictor:
    def __init__(self, lookback=60):
        self.lookback = lookback
        self.model = None
        self.scaler = MinMaxScaler()

    def prepare_data(self, df, target="close"):
        data = df[target].values.reshape(-1, 1)
        data_scaled = self.scaler.fit_transform(data)
        X, y = [], []
        for i in range(self.lookback, len(data_scaled)):
            X.append(data_scaled[i - self.lookback : i, 0])
            y.append(data_scaled[i, 0])
        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        model = Sequential(
            [
                LSTM(50, return_sequences=True, input_shape=(input_shape[0], 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(1),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        self.model = model
        return model

    def train(self, X, y, epochs=50, batch_size=32):
        es = EarlyStopping(patience=5, restore_best_weights=True)
        self.model.fit(
            X,
            y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            callbacks=[es],
            verbose=0,
        )

    def predict(self, X):
        return self.scaler.inverse_transform(self.model.predict(X, verbose=0))
