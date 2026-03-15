import pandas as pd
import numpy as np
import logging
from ..data.storage import Storage

logging.basicConfig(level=logging.INFO, format='[FeatureEngine] %(message)s')

class FeatureEngineerPro:
    def __init__(self, storage=None, window=14):
        self.storage = storage or Storage(base_dir="features_storage")
        self.window = window

    # -------------------
    # Feature de base
    # -------------------
    def compute_momentum(self, df, window=None):
        window = window or self.window
        df[f'momentum_{window}'] = df['close'].pct_change(periods=window)
        return df

    def compute_volatility(self, df, window=None):
        window = window or self.window
        df['returns'] = df['close'].pct_change()
        df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
        return df

    def compute_volume_spike(self, df, window=None):
        window = window or self.window
        df[f'volume_spike_{window}'] = df['volume'] / df['volume'].rolling(window=window).mean()
        return df

    # -------------------
    # Orderbook Imbalance (CEX uniquement)
    # -------------------
    def compute_orderbook_imbalance(self, df_orderbook):
        if df_orderbook is None or df_orderbook.empty:
            return pd.Series()
        imbalance = (df_orderbook['bids'].sum(axis=1) - df_orderbook['asks'].sum(axis=1)) / \
                    (df_orderbook['bids'].sum(axis=1) + df_orderbook['asks'].sum(axis=1))
        return imbalance

    # -------------------
    # Whale activity
    # -------------------
    def compute_whale_activity(self, df, multiplier=3):
        df['whale_activity'] = (df['volume'] > multiplier * df['volume'].rolling(self.window).mean()).astype(int)
        return df

    # -------------------
    # Normalisation
    # -------------------
    def normalize_features(self, df, feature_cols):
        for col in feature_cols:
            df[f'{col}_norm'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min() + 1e-9)
        return df

    # -------------------
    # Target / future return
    # -------------------
    def add_target(self, df, horizon=1):
        df[f'target_{horizon}'] = df['close'].shift(-horizon) / df['close'] - 1
        return df

    # -------------------
    # Multi-symbol features (corrélation)
    # -------------------
    def compute_cross_symbol_correlation(self, df1, df2, feature='returns'):
        corr = df1[feature].rolling(self.window).corr(df2[feature])
        return corr

    # -------------------
    # Pipeline complet
    # -------------------
    def compute_all_features(self, df, df_orderbook=None, add_target=True, horizon=1):
        df = self.compute_momentum(df)
        df = self.compute_volatility(df)
        df = self.compute_volume_spike(df)
        if df_orderbook is not None:
            df['orderbook_imbalance'] = self.compute_orderbook_imbalance(df_orderbook)
        df = self.compute_whale_activity(df)
        feature_cols = [c for c in df.columns if c not in ['timestamp', 'returns']]
        df = self.normalize_features(df, feature_cols)
        if add_target:
            df = self.add_target(df, horizon=horizon)
        df = df.drop(columns=['returns'], errors='ignore')
        return df

    # -------------------
    # Save features CSV versionné
    # -------------------
    def save_features(self, df, symbol, timeframe, source, version=1):
        filename = f"{symbol}_{source}_{timeframe}_features_v{version}.csv"
        self.storage.save_csv(df, filename)
