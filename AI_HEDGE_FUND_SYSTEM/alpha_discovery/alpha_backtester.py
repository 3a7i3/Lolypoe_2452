import pandas as pd

class AlphaBacktester:
    def __init__(self, price_col="close"):
        self.price_col = price_col

    def run(self, df, signal, fee=0.0):
        """
        Backtest simple : long si signal==1, flat sinon.
        - df: DataFrame avec prix
        - signal: pandas.Series alignée sur df
        - fee: frais de transaction (proportionnel, ex: 0.001 pour 0.1%)
        Retourne un DataFrame avec equity curve et stats.
        """
        returns = df[self.price_col].pct_change().shift(-1).fillna(0)
        position = signal.shift(1).fillna(0)  # On prend le signal à la clôture précédente
        gross = position * returns
        # Frais si changement de position
        trades = position.diff().abs().fillna(0)
        net = gross - trades * fee
        equity = (1 + net).cumprod()
        stats = {
            "total_return": equity.iloc[-1] - 1,
            "sharpe": net.mean() / (net.std() + 1e-8) * (252 ** 0.5),
            "max_drawdown": (equity.cummax() - equity).max()
        }
        return pd.DataFrame({"equity": equity, "net": net, "position": position}), stats
