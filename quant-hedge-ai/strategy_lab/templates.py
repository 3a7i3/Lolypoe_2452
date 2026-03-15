# templates.py
class StrategyTemplate:
    def __init__(self, name, logic):
        self.name = name
        self.logic = logic  # Fonction ou string à parser

    def inject_params(self, params):
        """
        Injecte les paramètres dans le template.
        """
        raise NotImplementedError
