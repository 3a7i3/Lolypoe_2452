class ChiefResearchAI:
    """Coordonne le cycle complet du laboratoire quant."""
    def __init__(self, agents):
        self.agents = agents

    def run_cycle(self, market_data):
        report = self.agents['market_analyst'].analyze(market_data)
        strategies = self.agents['strategy_scientist'].generate_strategies(report)
        backtest_results = self.agents['backtest_engineer'].backtest(strategies, market_data)
        risk_report = self.agents['risk_analyst'].analyze(backtest_results)
        allocation = self.agents['portfolio_manager'].allocate(backtest_results, risk_report)
        execution_report = self.agents['execution_trader'].execute(allocation)
        return {
            'market_report': report,
            'strategies': strategies,
            'backtest': backtest_results,
            'risk': risk_report,
            'allocation': allocation,
            'execution': execution_report
        }
