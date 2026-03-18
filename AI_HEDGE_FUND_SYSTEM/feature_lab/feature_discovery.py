import pandas as pd
import itertools

class FeatureDiscovery:
    def generate_combinations(self, df, max_comb=2):
        features = list(df.columns)
        combos = list(itertools.combinations(features, max_comb))
        new_features = {}
        for c in combos:
            name = "_x_".join(c)
            new_features[name] = df[c[0]] * df[c[1]]
        return pd.DataFrame(new_features)
