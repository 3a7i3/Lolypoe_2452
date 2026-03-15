from typing import List, Dict, Any

class BotDoctor:
    """
    Vérifie les stratégies avant backtesting ou trading réel :
    - Détecte erreurs logiques
    - Identifie stratégies à risque élevé
    - Valide stratégies robustes
    """

    def __init__(self):
        pass

    # -------------------------
    # Vérification de base
    # -------------------------
    def basic_validation(self, strategy: Dict[str, Any]) -> bool:
        """
        Vérifie la cohérence des paramètres de la stratégie
        """
        signal_type = strategy.get("signal_type")
        if signal_type not in ["momentum", "breakout", "mean_reversion"]:
            print(f"Invalid signal type: {signal_type}")
            return False

        # Exemple vérification RSI pour momentum
        if signal_type == "momentum":
            if not (0 <= strategy.get("rsi_buy", 0) <= 100):
                print(f"RSI buy invalide: {strategy.get('rsi_buy')}")
                return False
            if not (0 <= strategy.get("rsi_sell", 0) <= 100):
                print(f"RSI sell invalide: {strategy.get('rsi_sell')}")
                return False

        return True

    # -------------------------
    # Détection stratégies risquées
    # -------------------------
    def risk_check(self, strategy: Dict[str, Any]) -> bool:
        """
        Détecte stratégies potentiellement dangereuses
        """
        weight = strategy.get("weight", 1.0)
        if weight > 3.0 or weight < 0.1:
            print(f"Stratégie à risque : weight = {weight}")
            return False

        # Ajouter d'autres checks : drawdown simulé, paramètres extrêmes...
        return True

    # -------------------------
    # Validation complète
    # -------------------------
    def validate_strategies(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retourne seulement les stratégies robustes et valides
        """
        validated = []
        for strat in population:
            if self.basic_validation(strat) and self.risk_check(strat):
                validated.append(strat)
        print(f"{len(validated)}/{len(population)} stratégies validées")
        return validated

if __name__ == "__main__":
    population = [
        {"signal_type": "momentum", "rsi_buy": 30, "rsi_sell": 70, "weight": 1.0},
        {"signal_type": "breakout", "lookback_period": 20, "weight": 5.0},  # trop risquée
        {"signal_type": "mean_reversion", "lookback_period": 20, "threshold": 0.02, "weight": 1.1},
        {"signal_type": "unknown", "weight": 1.0},  # invalide
    ]

    doctor = BotDoctor()
    validated_population = doctor.validate_strategies(population)
    for strat in validated_population:
        print(strat)
