class AutonomousResearchLoop:
    def __init__(self, research_agent, strategy_farm, backtest_engine, bot_doctor, portfolio_engine):
        self.research_agent = research_agent
        self.strategy_farm = strategy_farm
        self.backtest_engine = backtest_engine
        self.bot_doctor = bot_doctor
        self.portfolio_engine = portfolio_engine

    def run_cycle(self):
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
        return approved
