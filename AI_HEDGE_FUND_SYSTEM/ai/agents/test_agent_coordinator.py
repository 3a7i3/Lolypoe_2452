from AI_HEDGE_FUND_SYSTEM.ai.agents.agent_coordinator import AgentCoordinator

def test_run_cycle():
    coordinator = AgentCoordinator()
    allocations = coordinator.run_cycle()
    assert allocations is not None
    print("Test passed: AgentCoordinator cycle runs.")

if __name__ == "__main__":
    test_run_cycle()
