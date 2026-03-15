class MarketUniverse:
    def __init__(self):
        # Marchés tradés pour le trading réel / paper trading
        self.trading_markets = {
            "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "forex": ["EURUSD", "USDJPY", "GBPUSD"],
            "stocks": ["AAPL", "MSFT", "NVDA"]
        }
        # Marchés pour recherche / apprentissage uniquement
        self.research_markets = {
            "memecoins": ["PEPE", "DOGE", "SHIB"],
            "microcaps": ["TINY1", "TINY2", "TINY3"]
        }

    def get_all_trading_assets(self):
        """
        Retourne la liste complète de tous les actifs tradés
        """
        assets = []
        for market_assets in self.trading_markets.values():
            assets.extend(market_assets)
        return assets

    def get_research_assets(self):
        """
        Retourne la liste complète de tous les actifs de recherche
        """
        assets = []
        for market_assets in self.research_markets.values():
            assets.extend(market_assets)
        return assets

    def add_trading_asset(self, market_type: str, asset: str):
        """
        Ajouter un actif à un marché tradé
        """
        if market_type in self.trading_markets:
            self.trading_markets[market_type].append(asset)
        else:
            self.trading_markets[market_type] = [asset]

    def add_research_asset(self, market_type: str, asset: str):
        """
        Ajouter un actif à un marché de recherche
        """
        if market_type in self.research_markets:
            self.research_markets[market_type].append(asset)
        else:
            self.research_markets[market_type] = [asset]

if __name__ == "__main__":
    from supervision.alert_manager import AlertManager
    alert_manager = AlertManager()
    universe = MarketUniverse()

    alert_manager.add_alert("=== Trading Assets ===")
    alert_manager.add_alert(str(universe.get_all_trading_assets()))

    alert_manager.add_alert("=== Research Assets ===")
    alert_manager.add_alert(str(universe.get_research_assets()))

    # Ajouter un actif et tester
    universe.add_trading_asset("crypto", "ADAUSDT")
    universe.add_research_asset("memecoins", "ELON")

    alert_manager.add_alert("=== Updated Trading Assets ===")
    alert_manager.add_alert(str(universe.get_all_trading_assets()))

    alert_manager.add_alert("=== Updated Research Assets ===")
    alert_manager.add_alert(str(universe.get_research_assets()))
