import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from utils.logger import logger

class AIModel:
    """Modele IA pour prediction des prix."""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=10, max_depth=5)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, df):
        """Prepare les features pour le modele."""
        try:
            features = df[['Close', 'Volume', 'RSI', 'SMA20', 'SMA50']].dropna()
            return self.scaler.fit_transform(features)
        except Exception as e:
            logger.error(f"Erreur preparation features: {e}")
            return None
    
    def train(self, X, y):
        """Entraine le modele."""
        try:
            self.model.fit(X, y)
            self.is_trained = True
            logger.info("Modele IA entraine")
        except Exception as e:
            logger.error(f"Erreur training: {e}")
    
    def predict(self, X):
        """Effectue une prediction."""
        try:
            if not self.is_trained:
                logger.warning("Modele non entraine")
                return None
            return self.model.predict(X)
        except Exception as e:
            logger.error(f"Erreur prediction: {e}")
            return None
