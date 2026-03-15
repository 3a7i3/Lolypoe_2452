import numpy as np

def normalize_series(series):
    """Normalize une série entre 0 et 1"""
    return (series - series.min()) / (series.max() - series.min())
