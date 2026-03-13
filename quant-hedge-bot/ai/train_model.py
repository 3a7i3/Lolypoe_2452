"""
Train Model - Entrainement des modeles ML
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from config import TEST_SIZE, VALIDATION_SIZE
from utils.logger import logger

class ModelTrainer:
    """Entraine les modeles."""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.model = None
    
    def prepare_data(self, data, target_col='Close'):
        """Prepare les donnees."""
        X = data.drop(columns=[target_col]).values
        y = data[target_col].values
        
        # Normaliser
        X_scaled = self.scaler.fit_transform(X)
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y,
            test_size=TEST_SIZE,
            shuffle=False
        )
        
        # Split validation
        X_val, X_test, y_val, y_test = train_test_split(
            X_test, y_test,
            test_size=0.5,
            shuffle=False
        )
        
        return {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test
        }
    
    def train_random_forest(self, data):
        """Entraine un Random Forest."""
        logger.info("Training Random Forest...")
        
        split_data = self.prepare_data(data)
        
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(split_data['X_train'], split_data['y_train'])
        
        # Eval
        train_score = self.model.score(split_data['X_train'], split_data['y_train'])
        test_score = self.model.score(split_data['X_test'], split_data['y_test'])
        
        logger.info(f"RF Train R2: {train_score:.4f}, Test R2: {test_score:.4f}")
        
        return self.model
    
    def predict(self, X):
        """Fait une prediction."""
        if self.model is None:
            logger.error("Model not trained")
            return None
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
