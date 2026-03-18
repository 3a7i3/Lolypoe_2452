# Niveau 6 — GenerativeAI (simulateur)
import random

class GenerativeAI:
    def __init__(self, base_prompt="Créer une stratégie alpha", default_params=None):
        self.base_prompt = base_prompt
        self.default_params = default_params or {"risk": "medium", "horizon": "short", "asset": "crypto"}

    def generate_strategy(self, prompt=None, params=None):
        # Simule la génération d’une stratégie basée sur un prompt et des paramètres dynamiques
        p = prompt or self.base_prompt
        par = self.default_params.copy()
        if params:
            par.update(params)
        # Génère un nom unique basé sur le prompt et les paramètres
        param_str = "_".join(f"{k}{v}" for k, v in sorted(par.items()))
        return f"gen_{p.replace(' ', '')}_{param_str}_{random.randint(1000, 9999)}"
