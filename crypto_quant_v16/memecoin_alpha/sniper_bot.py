from typing import List, Dict, Any
import random
import time

class SniperBot:
    """
    Exécute automatiquement l'achat des nouveaux tokens détectés.
    """

    def __init__(self, mode: str = "paper"):
        """
        mode: "paper" ou "real"
        """
        self.mode = mode
        self.trade_log = []

    # -------------------------
    # Exécution d'un achat sur un token
    # -------------------------
    def buy_token(self, token: str, capital: float, price: float, hype_score: float, rug_risk: str):
        """
        Exécute ou simule l'achat
        """
        # Ne pas acheter si rug risk élevé
        if rug_risk == "high":
            return {"token": token, "status": "skipped_high_risk"}

        # Calcul du nombre de tokens à acheter
        position_size = capital / price

        trade = {
            "token": token,
            "capital": capital,
            "price": price,
            "position_size": position_size,
            "hype_score": hype_score,
            "rug_risk": rug_risk,
            "mode": self.mode
        }

        if self.mode == "paper":
            trade["status"] = "executed_simulated"
        else:
            # Ici : appel API exchange pour exécution réelle
            trade["status"] = "executed_real"

        self.trade_log.append(trade)
        return trade

    # -------------------------
    # Exécution du portefeuille de tokens détectés
    # -------------------------
    def execute_token_report(self, token_report: Dict[str, Dict[str, Any]], capital_per_token: float = 1000, current_price: float = 1.0):
        executed_trades = []
        for token, info in token_report.items():
            trade = self.buy_token(
                token=token,
                capital=capital_per_token,
                price=current_price,
                hype_score=info.get("hype_score_social", 0),
                rug_risk=info.get("rug_risk", "low")
            )
            executed_trades.append(trade)
            time.sleep(0.1)  # simuler délai minimal pour éviter surcharges API
        return executed_trades

    # -------------------------
    # Historique des trades
    # -------------------------
    def get_trade_log(self):
        return self.trade_log

if __name__ == "__main__":
    from memecoin_detection import MemecoinDetectionSystem

    detector = MemecoinDetectionSystem()
    token_report = detector.generate_token_report_extended()

    bot = SniperBot(mode="paper")
    trades = bot.execute_token_report(token_report, capital_per_token=500, current_price=0.5)

    for t in trades:
        print(t)

    print("Historique complet :", bot.get_trade_log())
