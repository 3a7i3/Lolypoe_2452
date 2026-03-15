
import pandas as pd

class AlphaTester:
    def test(self, signal, returns):
        aligned = pd.concat([signal, returns], axis=1).dropna()
        corr = aligned.corr().iloc[0,1]
        return corr
