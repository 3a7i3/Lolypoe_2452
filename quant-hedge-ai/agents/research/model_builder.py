from __future__ import annotations


class ModelBuilder:
    """Toy ML model manager used for autonomous retraining cycles."""

    def __init__(self) -> None:
        self.version = 0
        self.last_score = 0.0

    def retrain(self, top_results: list[dict]) -> dict:
        self.version += 1
        if not top_results:
            return {"model_version": self.version, "training_score": 0.0}

        score = sum(float(x.get("sharpe", 0.0)) for x in top_results[:10]) / min(len(top_results), 10)
        self.last_score = score
        return {"model_version": self.version, "training_score": round(score, 4)}
