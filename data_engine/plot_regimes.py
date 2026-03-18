import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_engine.market_regime import MarketRegimeDetector

def plot_regimes_and_performance(df, equity_curve):
    regime_detector = MarketRegimeDetector()
    regimes = []
    for i in range(50, len(df)):
        sub_df = df.iloc[:i+1]
        regime = regime_detector.detect(sub_df)
        regimes.append(regime)
    # Align equity curve and regimes
    equity_curve = equity_curve[50:]
    dates = df.index[50:]
    regime_colors = {
        'bull': 'green',
        'bear': 'red',
        'range': 'blue',
        'high_volatility': 'orange'
    }
    plt.figure(figsize=(14, 6))
    for regime in set(regimes):
        idx = [i for i, r in enumerate(regimes) if r == regime]
        plt.plot(np.array(dates)[idx], np.array(equity_curve)[idx], label=regime, color=regime_colors.get(regime, 'gray'))
    plt.title('Equity Curve by Market Regime')
    plt.xlabel('Time')
    plt.ylabel('Equity')
    plt.legend()
    plt.tight_layout()
    plt.show()

# Exemple d'utilisation :
# df = ... (votre DataFrame de marché)
# equity_curve = ... (votre courbe d'équité)
# plot_regimes_and_performance(df, equity_curve)
