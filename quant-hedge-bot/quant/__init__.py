"""Quantitative research modules"""

from .backtester import Backtester
from .optimizer import StrategyOptimizer
from .feature_engineering import FeatureEngineering
from .regime_detection import RegimeDetector
from .anomaly_detection import AnomalyDetector

__all__ = [
    'Backtester',
    'StrategyOptimizer',
    'FeatureEngineering',
    'RegimeDetector',
    'AnomalyDetector'
]
