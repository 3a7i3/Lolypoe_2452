from .alpha_tester import AlphaTester

class AlphaCluster:
    def mine(self, features, returns):
        tester = AlphaTester()
        results = {}
        for name, feature in features.items():
            signal = feature.apply(lambda x: 1 if x > 0 else -1)
            score = tester.test(signal, returns)
            results[name] = score
        return results
