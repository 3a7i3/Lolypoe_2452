from ai.agents.agent_coordinator import AgentCoordinator
import time

def main():
    coordinator = AgentCoordinator()
    while True:
        print("\n=== New Quant Organism Cycle ===")
        coordinator.run_cycle()
        time.sleep(60)  # Pause entre les cycles (modifiable)

if __name__ == "__main__":
    main()
