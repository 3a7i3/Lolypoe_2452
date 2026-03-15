# parameter_space.py
class ParameterSpace:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name

    def get_grid(self):
        """
        Retourne la grille de paramètres à explorer pour la stratégie.
        """
        raise NotImplementedError
