"""
Module analyze_results : analyse la performance des stratégies à partir des résultats collectés.
"""

class ResultAnalyzer:
    def __init__(self):
        pass

    def analyze(self, results):
        trades = results.get('trades', [])
        if not trades:
            return {'performance': 'no_data', 'summary': {}}
        # Calculs simples pour l'exemple
        total_pnl = sum(t['pnl'] for t in trades)
        avg_sharpe = sum(t['sharpe'] for t in trades) / len(trades)
        best_strategy = max(trades, key=lambda t: t['pnl'])['strategy']
        worst_strategy = min(trades, key=lambda t: t['pnl'])['strategy']
        return {
            'performance': 'analyzed',
            'summary': {
                'total_pnl': total_pnl,
                'avg_sharpe': avg_sharpe,
                'best_strategy': best_strategy,
                'worst_strategy': worst_strategy,
                'n_strategies': len(trades)
            }
        }

# Test minimal du module
if __name__ == '__main__':
    analyzer = ResultAnalyzer()
    fake_results = {
        'trades': [
            {'strategy': 'A', 'pnl': 1.2, 'sharpe': 1.1},
            {'strategy': 'B', 'pnl': -0.5, 'sharpe': -0.2},
            {'strategy': 'C', 'pnl': 0.7, 'sharpe': 0.8}
        ]
    }
    analysis = analyzer.analyze(fake_results)
    assert analysis['performance'] == 'analyzed'
    assert analysis['summary']['best_strategy'] == 'A'
    print('analyze_results OK:', analysis)
