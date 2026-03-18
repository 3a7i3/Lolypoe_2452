class AutonomousResearchLoop:
            # Alerte Telegram si feedback critique
            try:
                import requests
                TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
                TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
                alert_needed = False
                alert_msg = None
                if feedback_report.get("max_drawdown", 0) > 0.2:
                    alert_needed = True
                    alert_msg = f"[ALERTE R&D] Drawdown élevé détecté : {feedback_report.get('max_drawdown', 0):.2%}"
                if "stagnation" in " ".join(feedback_report.get("insights", [])):
                    alert_needed = True
                    alert_msg = "[ALERTE R&D] Stagnation détectée dans la recherche de stratégies."
                if alert_needed and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": alert_msg}
                    requests.post(url, data=payload, timeout=5)
                    print("[ALERTE] Notification Telegram envoyée.")
            except Exception as e:
                print(f"[ALERTE] Erreur envoi Telegram : {e}")
    def __init__(self, research_agent, strategy_farm, backtest_engine, bot_doctor, portfolio_engine):
        self.research_agent = research_agent
        self.strategy_farm = strategy_farm
        self.backtest_engine = backtest_engine
        self.bot_doctor = bot_doctor
        self.portfolio_engine = portfolio_engine

    def run_cycle(self):
        from ai_autonomous_loop.performance_feedback import PerformanceFeedback
        from ai_autonomous_loop.auto_optimizer import HyperparameterOptimizer
        # 1. Générer des hypothèses
        hypotheses = self.research_agent.generate_hypotheses()
        # 2. Créer des stratégies
        strategies = self.strategy_farm.generate(hypotheses)
        # 3. Massive backtest
        results = self.backtest_engine.run(strategies)
        # 4. Validation
        approved = self.bot_doctor.validate(results)
        # 5. Mise à jour du portefeuille
        self.portfolio_engine.update(approved)
        # 6. Feedback automatique
        feedback_agent = PerformanceFeedback()
        feedback_report = feedback_agent.analyze(approved)
        print("[Feedback R&D]", feedback_report)

        # Export feedback en JSON à chaque cycle
        import json
        from pathlib import Path
        from datetime import datetime
        output_dir = "feedback_logs"
        Path(output_dir).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_{timestamp}.json"
        with open(Path(output_dir) / filename, "w", encoding="utf-8") as f:
            json.dump(feedback_report, f, indent=2, ensure_ascii=False)

        # 7. Prise de décision automatique selon le feedback
        action_taken = None
        if "diversité" in " ".join(feedback_report.get("insights", [])):
            print("[AUTO] Relance génération avec plus de diversité.")
            extra_hypotheses = self.research_agent.generate_hypotheses() + ["hybrid", "multi_factor"]
            strategies = self.strategy_farm.generate(extra_hypotheses)
            results = self.backtest_engine.run(strategies)
            approved = self.bot_doctor.validate(results)
            self.portfolio_engine.update(approved)
            action_taken = "relance_diversite"
        elif "optimiser" in " ".join(feedback_report.get("exploration", [])):
            print("[AUTO] Optimisation des hyperparamètres sur les top stratégies.")
            optimizer = HyperparameterOptimizer(self.strategy_farm)
            optimized = optimizer.optimize([s["id"] for s in approved])
            # Génère et backtest les variantes optimisées
            strategies = self.strategy_farm.generate([o["base"] for o in optimized])
            results = self.backtest_engine.run(strategies)
            approved = self.bot_doctor.validate(results)
            self.portfolio_engine.update(approved)
            action_taken = "optimisation_hyperparametres"
        else:
            print("[AUTO] Aucun ajustement automatique nécessaire.")
            action_taken = "none"

        return {"approved": approved, "feedback": feedback_report, "action": action_taken}
