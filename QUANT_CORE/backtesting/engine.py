"""
BacktestEngine stub for QUANT_CORE
"""
class BacktestEngine:
    def __init__(self):
        pass

    def run(self, strategy, data, features):
        """Exécute le backtest d'une stratégie sur les données et features."""
        # Simulation simple : appliquer la stratégie sur les données
        results = []
        for idx, row in data.iterrows():
            signal = strategy.get('signal_func', lambda x: 0)(row, features)
            # Exécution fictive : buy/sell/hold
            results.append({
                'timestamp': idx,
                'signal': signal,
                'price': row['Close'],
                'volume': row.get('Volume', 0)
            })
        # Calcul des métriques de performance
        metrics = self.calculate_metrics(results)
        return {'approved': True, 'metrics': metrics, 'results': results}

    def calculate_metrics(self, results):
        """Calcule les métriques de performance du backtest."""
        # Exemple : rendement, drawdown, ratio gain/perte
        prices = [r['price'] for r in results]
        signals = [r['signal'] for r in results]
        returns = [0]
        for i in range(1, len(prices)):
            if signals[i-1] == 1:  # buy
                returns.append(prices[i] - prices[i-1])
            elif signals[i-1] == -1:  # sell
                returns.append(prices[i-1] - prices[i])
            else:
                returns.append(0)
        total_return = sum(returns)
        max_drawdown = min(returns)
        win_ratio = sum(1 for r in returns if r > 0) / max(1, len(returns))
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'win_ratio': win_ratio
        }
