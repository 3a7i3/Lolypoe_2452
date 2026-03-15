"""
Analyzer for historical crash data (AI-quant enhanced).
"""

import numpy as np
import scipy.stats as stats

class CrashAnalyzer:
    def __init__(self):
        pass

    def analyze(self, crash_events):
        """Advanced analysis: volatility, drawdown, skewness, kurtosis, volume spike, rolling correlation, AI scoring."""
        results = []
        for event in crash_events:
            prices = np.array(event.get('prices', []), dtype=float)
            volumes = np.array(event.get('volumes', []), dtype=float)
            name = event.get('name', 'Unknown')
            if len(prices) < 2:
                continue
            # Returns
            returns = np.diff(prices) / prices[:-1]
            volatility = float(np.std(returns))
            annualized_vol = volatility * np.sqrt(252)  # daily to annual
            # Max drawdown
            running_max = np.maximum.accumulate(prices)
            drawdowns = (prices - running_max) / running_max
            max_drawdown = float(np.min(drawdowns))
            # Skewness & kurtosis
            skew = float(stats.skew(returns)) if len(returns) > 2 else 0.0
            kurt = float(stats.kurtosis(returns)) if len(returns) > 2 else 0.0
            # Volume spike detection
            avg_volume = float(np.mean(volumes)) if len(volumes) > 0 else 0.0
            max_volume = float(np.max(volumes)) if len(volumes) > 0 else 0.0
            volume_spike = (max_volume / avg_volume) if avg_volume > 0 else 0.0
            # Rolling correlation (if extra data provided)
            corr = None
            if 'benchmark_prices' in event:
                bench = np.array(event['benchmark_prices'], dtype=float)
                min_len = min(len(prices), len(bench))
                if min_len > 5:
                    corr = float(np.corrcoef(prices[-min_len:], bench[-min_len:])[0,1])
            # AI scoring (simple): combine risk metrics
            risk_score = -max_drawdown * annualized_vol * (1 + abs(skew) + kurt/3)
            # AI summary
            summary = (
                f"Crash: {name}\n"
                f"- Annualized Volatility: {annualized_vol:.2%}\n"
                f"- Max Drawdown: {max_drawdown:.2%}\n"
                f"- Skewness: {skew:.2f}, Kurtosis: {kurt:.2f}\n"
                f"- Volume Spike: {volume_spike:.2f}\n"
                + (f"- Rolling Correlation: {corr:.2f}\n" if corr is not None else "")
                + f"- AI Risk Score: {risk_score:.2f}\n"
            )
            results.append({
                'name': name,
                'annualized_volatility': annualized_vol,
                'max_drawdown': max_drawdown,
                'skewness': skew,
                'kurtosis': kurt,
                'volume_spike': volume_spike,
                'rolling_correlation': corr,
                'ai_risk_score': risk_score,
                'summary': summary,
            })
        return results

if __name__ == "__main__":
    # Exemple de test avancé
    crash_events = [
        {
            'name': 'Black Monday 1987',
            'prices': [100, 98, 80, 70, 60, 62, 65],
            'volumes': [1000, 1200, 3000, 5000, 7000, 4000, 2000],
            'benchmark_prices': [100, 99, 90, 85, 80, 83, 90],
        },
        {
            'name': 'COVID-19 Crash 2020',
            'prices': [200, 180, 150, 120, 110, 130, 170],
            'volumes': [2000, 2500, 8000, 10000, 9000, 6000, 3000],
            'benchmark_prices': [200, 190, 170, 140, 130, 150, 180],
        },
    ]
    analyzer = CrashAnalyzer()
    results = analyzer.analyze(crash_events)
    for r in results:
        print(r['summary'])
