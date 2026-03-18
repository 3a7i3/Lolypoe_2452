import pandas as pd

class DatasetBuilder:
    def build(self, df):
        dataset = pd.DataFrame()
        dataset["rsi"] = df["rsi"]
        dataset["momentum"] = df["momentum"]
        dataset["volatility"] = df["volatility"]
        dataset["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
        dataset.dropna(inplace=True)
        return dataset
