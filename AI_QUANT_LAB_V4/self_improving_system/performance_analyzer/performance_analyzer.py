"""
Analyse avancée des performances des stratégies (Sharpe, drawdown, stabilité, etc.).
"""

class PerformanceAnalyzer:
    def __init__(self):
        pass

    def sharpe_analysis(self, trades):
        # Calcul simple du Sharpe moyen
        if not trades:
            return 0.0
        return sum(t['sharpe'] for t in trades) / len(trades)

    def drawdown_analysis(self, trades):
        # Simule un drawdown max sur la série de PnL
        pnl_series = [t['pnl'] for t in trades]
        max_drawdown = 0
        peak = float('-inf')
        for pnl in pnl_series:
            if pnl > peak:
                peak = pnl
            dd = peak - pnl
            if dd > max_drawdown:
                max_drawdown = dd
        return max_drawdown

    def stability_analysis(self, trades):
        # Mesure la variance des PnL comme proxy de stabilité
        if not trades:
            return 0.0
        mean = sum(t['pnl'] for t in trades) / len(trades)
        var = sum((t['pnl'] - mean) ** 2 for t in trades) / len(trades)
        return var

    def regime_performance(self, trades, regime='all'):
        # Placeholder pour analyse par régime de marché
        return {'regime': regime, 'n_trades': len(trades)}

# Test minimal du module
if __name__ == '__main__':
    analyzer = PerformanceAnalyzer()
    fake_trades = [
        {'strategy': 'A', 'pnl': 1.2, 'sharpe': 1.1},
        {'strategy': 'B', 'pnl': -0.5, 'sharpe': -0.2},
        {'strategy': 'C', 'pnl': 0.7, 'sharpe': 0.8}
    ]
    print('Sharpe:', analyzer.sharpe_analysis(fake_trades))
    print('Drawdown:', analyzer.drawdown_analysis(fake_trades))
    print('Stability:', analyzer.stability_analysis(fake_trades))
    print('Regime:', analyzer.regime_performance(fake_trades, 'bull'))
