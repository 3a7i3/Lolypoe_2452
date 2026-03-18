class AISignalGenerator:
    def __init__(self, model):
        self.model = model

    def generate(self, df):
        features = df[["rsi","momentum","volatility"]].iloc[-1:]
        prob = self.model.predict(features)
        if prob > 0.6:
            return "BUY"
        elif prob < 0.4:
            return "SELL"
        return "HOLD"
