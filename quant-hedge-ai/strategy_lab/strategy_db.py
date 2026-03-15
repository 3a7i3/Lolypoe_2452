# strategy_db.py
class StrategyDatabase:
    def __init__(self, db_path):
        self.db_path = db_path

    def save(self, strategy_id, params, metrics, rank):
        """
        Sauvegarde la stratégie et ses résultats.
        """
        raise NotImplementedError

    def top_strategies(self, n=50):
        """
        Retourne les n meilleures stratégies.
        """
        raise NotImplementedError
