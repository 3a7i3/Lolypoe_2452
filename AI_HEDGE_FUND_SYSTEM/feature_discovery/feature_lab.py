from .base_features import BaseFeatures
from .feature_generator import FeatureGenerator
from .feature_evaluator import FeatureEvaluator

class FeatureLab:
    def run(self, df):
        base = BaseFeatures().compute(df)
        generator = FeatureGenerator()
        evaluator = FeatureEvaluator()
        returns = df["close"].pct_change().shift(-1)
        results = {}
        columns = base.columns
        for i in range(len(columns)):
            for j in range(i+1, len(columns)):
                f1 = base[columns[i]]
                f2 = base[columns[j]]
                feature = generator.combine(f1, f2, "mul")
                score = evaluator.evaluate(feature, returns)
                name = f"{columns[i]}_mul_{columns[j]}"
                results[name] = score
        return results
