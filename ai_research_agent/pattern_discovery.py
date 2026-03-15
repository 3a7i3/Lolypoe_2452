class PatternDiscovery:
    def __init__(self, df, macro_data=None, sentiment_data=None, onchain_data=None):
        self.df = df
        self.macro_data = macro_data
        self.sentiment_data = sentiment_data
        self.onchain_data = onchain_data

    def find_patterns(self):
        patterns = {}
        returns = self.df["close"].pct_change()
        vol_cluster = returns.rolling(20).std()
        patterns["volatility_cluster"] = float(vol_cluster.iloc[-1])
        volume_spike = self.df["volume"].iloc[-1] > self.df["volume"].mean() * 2
        patterns["volume_spike"] = volume_spike

        # Liquidation cluster detection (ex: volume spike + price drop)
        if "liquidations" in self.df.columns:
            liq_cluster = self.df["liquidations"].rolling(10).sum().iloc[-1] > self.df["liquidations"].mean() * 3
            patterns["liquidation_cluster"] = liq_cluster

        # Whale activity (ex: large trades)
        if "large_trades" in self.df.columns:
            whale = self.df["large_trades"].iloc[-1] > self.df["large_trades"].mean() * 2
            patterns["whale_activity"] = whale

        # Regime shift (trend change)
        ma20 = self.df["close"].rolling(20).mean().iloc[-1]
        ma100 = self.df["close"].rolling(100).mean().iloc[-1]
        patterns["regime_shift"] = abs(ma20 - ma100) / ma100 > 0.05

        # Anomaly detection (price jump/drop)
        price_jump = abs(returns.iloc[-1]) > returns.std() * 3
        patterns["anomaly"] = price_jump

        # Macro data patterns
        if self.macro_data is not None:
            if self.macro_data.get("liquidity") == "tight":
                patterns["macro_liquidity_risk"] = True
            if self.macro_data.get("rate_hike"):
                patterns["macro_rate_hike"] = True

        # Sentiment data patterns
        if self.sentiment_data is not None:
            if self.sentiment_data.get("sentiment_score", 0) < -0.5:
                patterns["negative_sentiment"] = True
            if self.sentiment_data.get("news_fear"):
                patterns["news_fear"] = True

        # Onchain data patterns
        if self.onchain_data is not None:
            if self.onchain_data.get("exchange_inflow", 0) > 1e6:
                patterns["onchain_exchange_inflow"] = True
            if self.onchain_data.get("whale_transfer", 0) > 1e5:
                patterns["onchain_whale_transfer"] = True

        return patterns
