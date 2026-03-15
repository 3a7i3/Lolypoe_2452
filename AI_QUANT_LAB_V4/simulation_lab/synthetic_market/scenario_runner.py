from market_generator import MarketGenerator
from regime_simulator import RegimeSimulator
from crash_simulator import CrashSimulator
from whale_manipulation import WhaleManipulation
from liquidity_simulator import LiquidityCrisis

class ScenarioRunner:
    def run(self, regime="bull", with_crash=True):
        gen = MarketGenerator()
        reg = RegimeSimulator()
        crash = CrashSimulator()
        whale = WhaleManipulation()
        liquidity = LiquidityCrisis()
        params = reg.get_params(regime)
        df = gen.generate_price_series(drift=params["drift"], volatility=params["volatility"])
        df = whale.pump_dump(df)
        df = liquidity.simulate(df)
        if with_crash:
            df = crash.inject_crash(df)
        return df
