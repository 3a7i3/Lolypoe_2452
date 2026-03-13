# Ce module a été migré vers QUANT_CORE/strategy_lab/__init__.py
        markets: List[str] | None = None,
        timeframes: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Create initial population for multiple markets and timeframes."""
        market_universe = markets or ["crypto"]
        timeframe_universe = timeframes or ["5m", "15m", "1h", "4h"]

        self.population = [
            self._random_strategy(sid=i, markets=market_universe, timeframes=timeframe_universe)
            for i in range(size)
        ]
        logger.info("%s generated %d candidate strategies", self.name, size)
        return self.population

    def generate_signals(self, prices: np.ndarray, strategy: Dict[str, Any], regime: str = "NORMAL") -> np.ndarray:
        """Generate normalized signals from a weighted multi-indicator blend."""
        if prices.size < 30:
            return np.zeros_like(prices, dtype=float)

        params = strategy["params"]
        weights = strategy["weights"]
        score = np.zeros(prices.shape[0], dtype=float)

        if "RSI" in strategy["indicators"]:
            rsi = self._rsi(prices, period=int(params["rsi_period"]))
            score += (-(rsi - 50.0) / 50.0) * weights["RSI"]

        if "EMA" in strategy["indicators"]:
            fast = self._ema_series(prices, int(params["fast_ema"]))
            slow = self._ema_series(prices, int(params["slow_ema"]))
            spread = np.where(slow != 0, (fast - slow) / slow, 0.0)
            score += spread * weights["EMA"]

        if "MACD" in strategy["indicators"]:
            macd_hist = self._macd_hist(prices)
            score += macd_hist * weights["MACD"]

        if "BB" in strategy["indicators"]:
            bbz = self._bollinger_zscore(prices, int(params["bb_period"]))
            score += (-bbz) * weights["BB"]

        if "MOMENTUM" in strategy["indicators"]:
            mom = self._momentum(prices, int(params["momentum_period"]))
            score += mom * weights["MOMENTUM"]

        entry = float(params["entry_threshold"])
        exit_level = float(params["exit_threshold"])

        if regime == "HIGH_VOL":
            entry *= 1.15
            exit_level *= 1.15
        elif regime == "BULL":
            entry *= 0.9
        elif regime == "BEAR":
            entry *= 1.05

        signals = np.zeros(prices.shape[0], dtype=int)
        signals[score > entry] = 1
        signals[score < exit_level] = -1
        return signals

    def evaluate_fitness(
        self,
        strategies: List[Dict[str, Any]],
        evaluator: Callable[[Dict[str, Any]], Dict[str, float]],
    ) -> List[Dict[str, Any]]:
        """Evaluate strategy quality with drawdown and overfitting penalties."""
        evaluated: List[Dict[str, Any]] = []
        for strategy in strategies:
            metrics = evaluator(strategy)
            strategy["metrics"] = metrics
            strategy["fitness"] = self._score_metrics(metrics)
            evaluated.append(strategy)

        evaluated.sort(key=lambda x: x["fitness"], reverse=True)
        return evaluated

    def _score_metrics(self, metrics: Dict[str, float]) -> float:
        sharpe = float(metrics.get("sharpe", 0.0))
        sortino = float(metrics.get("sortino", sharpe))
        total_return = float(metrics.get("total_return", 0.0))
        max_drawdown = float(metrics.get("max_drawdown", 0.0))
        overfit_score = float(metrics.get("overfit_score", 0.0))

        drawdown_penalty = max(0.0, max_drawdown - 0.12) * 4.0
        return (1.2 * sharpe) + (0.6 * sortino) + (0.8 * total_return) - drawdown_penalty - overfit_score

    def select_best(self, population: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        return sorted(population, key=lambda x: x["fitness"], reverse=True)[:top_n]

    def crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        child = copy.deepcopy(parent1 if self._rng.random() < 0.5 else parent2)
        child["id"] = self._rng.randint(1_000_000, 9_999_999)
        child["generation"] = self.generation

        child["market"] = self._rng.choice([parent1["market"], parent2["market"]])
        child["timeframe"] = self._rng.choice([parent1["timeframe"], parent2["timeframe"]])

        merged_indicators = list(dict.fromkeys(parent1["indicators"] + parent2["indicators"]))
        self._rng.shuffle(merged_indicators)
        child["indicators"] = merged_indicators[: self._rng.choice([2, 3])]

        child_weights: Dict[str, float] = {}
        for ind in child["indicators"]:
            w1 = parent1["weights"].get(ind, self._rng.uniform(0.1, 1.0))
            w2 = parent2["weights"].get(ind, self._rng.uniform(0.1, 1.0))
            child_weights[ind] = (float(w1) + float(w2)) / 2.0
        weight_sum = sum(child_weights.values()) or 1.0
        child["weights"] = {k: v / weight_sum for k, v in child_weights.items()}

        for key in child["params"]:
            v1 = parent1["params"][key]
            v2 = parent2["params"][key]
            child["params"][key] = (v1 + v2) / 2 if isinstance(v1, float) else int((v1 + v2) / 2)

        child["fitness"] = 0.0
        child["metrics"] = {}
        return child

    def mutate(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        s = copy.deepcopy(strategy)

        if self._rng.random() < 0.20:
            new_indicator = self._rng.choice(self.indicators)
            if new_indicator not in s["indicators"]:
                s["indicators"].append(new_indicator)
                s["indicators"] = s["indicators"][:3]

        if self._rng.random() < 0.25:
            key = self._rng.choice(list(s["params"].keys()))
            if key in {"rsi_period", "fast_ema", "slow_ema", "bb_period", "momentum_period"}:
                s["params"][key] = max(2, int(s["params"][key] + self._rng.randint(-5, 5)))
            else:
                s["params"][key] = round(float(s["params"][key]) + self._rng.uniform(-0.1, 0.1), 3)

        if self._rng.random() < 0.20:
            s["risk"]["max_position"] = float(np.clip(s["risk"]["max_position"] + self._rng.uniform(-0.03, 0.03), 0.03, 0.25))
            s["risk"]["risk_per_trade"] = float(np.clip(s["risk"]["risk_per_trade"] + self._rng.uniform(-0.005, 0.005), 0.003, 0.05))
            s["risk"]["max_drawdown_stop"] = float(np.clip(s["risk"]["max_drawdown_stop"] + self._rng.uniform(-0.03, 0.03), 0.08, 0.35))

        raw = np.array([self._rng.uniform(0.1, 1.0) for _ in s["indicators"]], dtype=float)
        raw = raw / raw.sum()
        s["weights"] = {k: float(v) for k, v in zip(s["indicators"], raw)}
        return s

    def evolve(
        self,
        population: List[Dict[str, Any]],
        evaluator: Callable[[Dict[str, Any]], Dict[str, float]],
        mutation_rate: float = 0.25,
        elite_size: int = 10,
    ) -> List[Dict[str, Any]]:
        self.generation += 1
        ranked = self.evaluate_fitness(population, evaluator)
        elite = ranked[: min(elite_size, len(ranked))]

        new_pop: List[Dict[str, Any]] = [copy.deepcopy(s) for s in elite]
        while len(new_pop) < len(population):
            if self._rng.random() < 0.75 and len(elite) >= 2:
                p1, p2 = self._rng.sample(elite, 2)
                child = self.crossover(p1, p2)
            else:
                child = copy.deepcopy(self._rng.choice(elite))

            if self._rng.random() < mutation_rate:
                child = self.mutate(child)
            new_pop.append(child)

        self.population = new_pop
        logger.info(
            "Generation %d complete. Best fitness=%.3f, sharpe=%.3f",
            self.generation,
            ranked[0]["fitness"],
            float(ranked[0].get("metrics", {}).get("sharpe", 0.0)),
        )
        return new_pop

    def grid_search_optimize(
        self,
        base_strategy: Dict[str, Any],
        evaluator: Callable[[Dict[str, Any]], Dict[str, float]],
        param_grid: Dict[str, List[Any]],
        max_evals: int = 96,
    ) -> Dict[str, Any]:
        """Local refinement around the best genetic candidate."""
        if not param_grid:
            return base_strategy

        keys = list(param_grid.keys())
        combos = list(itertools.product(*(param_grid[k] for k in keys)))
        self._rng.shuffle(combos)

        best = copy.deepcopy(base_strategy)
        best_metrics = evaluator(best)
        best["metrics"] = best_metrics
        best["fitness"] = self._score_metrics(best_metrics)

        for values in combos[:max_evals]:
            candidate = copy.deepcopy(base_strategy)
            for key, value in zip(keys, values):
                candidate["params"][key] = value

            candidate_metrics = evaluator(candidate)
            candidate_fitness = self._score_metrics(candidate_metrics)
            if candidate_fitness > float(best["fitness"]):
                best = candidate
                best["metrics"] = candidate_metrics
                best["fitness"] = candidate_fitness

        return best

    def get_best_strategies(self, top_n: int = 5) -> List[Dict[str, Any]]:
        return sorted(self.population, key=lambda x: x.get("fitness", 0.0), reverse=True)[:top_n]

    def _ema_series(self, prices: np.ndarray, period: int) -> np.ndarray:
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices, dtype=float)
        ema[0] = prices[0]
        for i in range(1, prices.size):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
        return ema

    def _rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        deltas = np.diff(prices, prepend=prices[0])
        gains = np.clip(deltas, 0.0, None)
        losses = np.clip(-deltas, 0.0, None)
        avg_gain = self._ema_series(gains, max(2, period))
        avg_loss = self._ema_series(losses, max(2, period))
        # Correction: évite division par zéro et valeurs invalides
        rs = np.zeros_like(avg_gain)
        valid = avg_loss > 1e-8
        rs[valid] = avg_gain[valid] / avg_loss[valid]
        # Clamp les valeurs invalides
        rs = np.nan_to_num(rs, nan=0.0, posinf=0.0, neginf=0.0)
        return 100.0 - (100.0 / (1.0 + rs))

    def _macd_hist(self, prices: np.ndarray) -> np.ndarray:
        ema12 = self._ema_series(prices, 12)
        ema26 = self._ema_series(prices, 26)
        macd_line = ema12 - ema26
        signal = self._ema_series(macd_line, 9)
        return macd_line - signal

    def _bollinger_zscore(self, prices: np.ndarray, period: int = 20) -> np.ndarray:
        series = np.asarray(prices, dtype=float)
        out = np.zeros(series.size, dtype=float)
        for i in range(period, series.size):
            window = series[i - period + 1 : i + 1]
            mean = float(window.mean())
            std = float(window.std())
            out[i] = (series[i] - mean) / std if std > 0 else 0.0
        return out

    def _momentum(self, prices: np.ndarray, period: int = 10) -> np.ndarray:
        period = max(1, int(period))
        out = np.zeros(prices.size, dtype=float)
        out[period:] = (prices[period:] - prices[:-period]) / np.maximum(prices[:-period], 1e-12)
        return out
