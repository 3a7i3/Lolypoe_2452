
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pandas as pd
from strategy_ai.dataset_builder import DatasetBuilder
from strategy_ai.model import StrategyAIModel
from strategy_ai.signal_generator import AISignalGenerator

def test_strategy_ai():
    n = 50
    df = pd.DataFrame({
        "rsi": [0.3, 0.5, 0.7, 0.6, 0.4]*(n//5),
        "momentum": [0.4, 0.6, 0.8, 0.7, 0.5]*(n//5),
        "volatility": [0.2, 0.3, 0.5, 0.4, 0.3]*(n//5),
        "close": [10, 11, 12, 11.5, 12.2]*(n//5)
    })
    builder = DatasetBuilder()
    dataset = builder.build(df)
    model = StrategyAIModel()
    model.train(dataset)
    signal_engine = AISignalGenerator(model)
    signal = signal_engine.generate(df)
    print(f"AI Signal: {signal}")
    assert signal in ["BUY", "SELL", "HOLD"]
    print("AI Strategy Brain test passed.")

if __name__ == "__main__":
    test_strategy_ai()
