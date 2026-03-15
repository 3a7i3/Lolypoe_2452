import pandas as pd
import ccxt  # pour exchanges centralisés
from typing import Dict, Any

class DataEngine:
    """
    Collecte et stocke toutes les données nécessaires pour le pipeline AI Quant Lab.
    """

    def __init__(self, market_universe):
        self.market_universe = market_universe
        self.data = {}  # stockage local : {asset: DataFrame}

        # Exemple : setup exchanges avec ccxt
        self.exchanges = {
            "binance": ccxt.binance({'enableRateLimit': True}),
            "kraken": ccxt.kraken({'enableRateLimit': True})
        }

    # -------------------------
    # Récupération OHLCV (prix)
    # -------------------------
    def fetch_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        exchange = self.exchanges.get(exchange_name)
        if exchange is None:
            raise ValueError(f"Exchange {exchange_name} non configuré")

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    # -------------------------
    # Collecte complète pour tous les assets
    # -------------------------
    def collect_all_data(self):
        # Assets tradés
        for asset in self.market_universe.get_all_trading_assets():
            try:
                # Ici on prend binance par défaut si disponible
                df = self.fetch_ohlcv("binance", asset)
                self.data[asset] = df
            except Exception as e:
                print(f"Erreur collecte {asset}: {e}")

        # Assets de recherche
        for asset in self.market_universe.get_research_assets():
            try:
                df = self.fetch_ohlcv("binance", asset)
                self.data[asset] = df
            except Exception as e:
                print(f"Erreur collecte recherche {asset}: {e}")

    # -------------------------
    # Récupérer un DataFrame pour un actif spécifique
    # -------------------------
    def get_data(self, asset: str) -> pd.DataFrame:
        return self.data.get(asset, pd.DataFrame())

    # -------------------------
    # Sauvegarde locale (CSV/Parquet)
    # -------------------------
    def save_data(self, asset: str, format: str = "csv"):
        df = self.get_data(asset)
        if df.empty:
            print(f"Aucune donnée pour {asset} à sauvegarder")
            return

        if format == "csv":
            df.to_csv(f"data_{asset}.csv", index=False)
        elif format == "parquet":
            df.to_parquet(f"data_{asset}.parquet", index=False)
        print(f"Données {asset} sauvegardées en {format}")

if __name__ == "__main__":
    from market_universe import MarketUniverse

    universe = MarketUniverse()
    data_engine = DataEngine(universe)

    # Collecte rapide pour tester
    data_engine.collect_all_data()

    # Vérifier BTCUSDT
    print(data_engine.get_data("BTCUSDT").head())

    # Sauvegarder en CSV
    data_engine.save_data("BTCUSDT", format="csv")
