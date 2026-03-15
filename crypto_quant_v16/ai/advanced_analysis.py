import io
import pandas as pd

# --- Panel dashboard interactif ---
try:
    import panel as pn
    pn.extension('matplotlib')

    def load_csv(file):
        if file is None:
            return None
        return pd.read_csv(io.BytesIO(file))

    file_input = pn.widgets.FileInput(accept='.csv')
    dashboard = pn.Column(
        pn.pane.Markdown("# Advanced Market Analysis Dashboard\nChargez un fichier CSV avec les colonnes 'close' et 'volume'."),
        file_input,
        pn.bind(lambda file: show_analysis(load_csv(file)), file_input)
    )

    if __name__ == "__main__":
        dashboard.servable()
        pn.serve(dashboard, port=5026, show=True)
except ImportError:
    pass

# ------------------------
# Classe AdvancedAnalysis (importable)
# ------------------------
import pandas as pd
import numpy as np
from typing import Dict, Any

class AdvancedAnalysis:
    """
    Analyse avancée pour la détection de signaux de marché :
    - Volatilité
    - Tendances
    - Liquidity / volume anomalies
    - Crash risk
    - Whale activity (placeholder)
    """

    def __init__(self, df: pd.DataFrame):
        """
        df doit contenir au minimum les colonnes : ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        self.df = df

    def volatility_analysis(self) -> Dict[str, Any]:
        returns = self.df["close"].pct_change()
        vol = returns.rolling(30).std().iloc[-1]
        regime = "high_volatility" if vol > 0.04 else "normal"
        return {"volatility_value": float(vol), "volatility_regime": regime}

    def trend_analysis(self) -> Dict[str, Any]:
        ma50 = self.df["close"].rolling(50).mean().iloc[-1]
        ma200 = self.df["close"].rolling(200).mean().iloc[-1]
        trend = "bull" if ma50 > ma200 else "bear"
        strength = abs(ma50 - ma200) / ma200
        return {"trend": trend, "trend_strength": float(strength)}

    def liquidity_analysis(self) -> Dict[str, Any]:
        volume = self.df["volume"].rolling(30).mean().iloc[-1]
        liquidity = "low" if volume < self.df["volume"].quantile(0.25) else "normal"
        return {"liquidity": liquidity, "avg_volume": float(volume)}

    def crash_risk_estimator(self) -> Dict[str, Any]:
        returns = self.df["close"].pct_change()
        volatility = returns.std()
        downside = returns[returns < 0].std()
        crash_risk = downside / volatility if volatility > 0 else 0
        return {"crash_probability": float(crash_risk)}

    def whale_activity_detection(self) -> Dict[str, Any]:
        # Placeholder : à améliorer plus tard avec wallet tracking
        return {"whale_activity": "accumulation"}

    def generate_market_report(self) -> Dict[str, Any]:
        report = {}
        report.update(self.volatility_analysis())
        report.update(self.trend_analysis())
        report.update(self.liquidity_analysis())
        report.update(self.crash_risk_estimator())
        report.update(self.whale_activity_detection())
        return report

# ------------------------
# Exemple d'utilisation (main)
# ------------------------
if __name__ == "__main__":
    # Exemple simple : données simulées
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=200, freq="H"),
        "open": np.random.rand(200) * 100,
        "high": np.random.rand(200) * 100,
        "low": np.random.rand(200) * 100,
        "close": np.random.rand(200) * 100,
        "volume": np.random.rand(200) * 1000
    }
    df = pd.DataFrame(data)

    analysis = AdvancedAnalysis(df)
    report = analysis.generate_market_report()
    from supervision.alert_manager import AlertManager
    alert_manager = AlertManager()
    alert_manager.add_alert(str(report))




# --- Panel dashboard interactif ---
# ...existing code...

# Bloc d'exemple d'utilisation à la toute fin
if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    from supervision.alert_manager import AlertManager
    alert_manager = AlertManager()
    np.random.seed(42)
    n = 300
    # Génère des prix simulés (marche aléatoire)
    prices = np.cumsum(np.random.randn(n)) + 100
    # Génère des volumes avec quelques spikes
    volumes = np.random.normal(1000, 200, n)
    volumes[::50] += 2000  # Spikes réguliers
    df = pd.DataFrame({
        "close": prices,
        "volume": volumes
    })
    analysis = AdvancedMarketAnalysis(df)
    alert_manager.add_alert("\n===== RAPPORT QUANTITATIF =====")
    report = analysis.generate_market_report()
    for k, v in report.items():
        alert_manager.add_alert(f"{k:20}: {v}")
    alert_manager.add_alert("===============================\n")
    alert_manager.add_alert("Affichage des graphiques...")
    analysis.visualize_market()
