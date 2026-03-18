from ecosystem.simulation import EcosystemSimulation

sim = EcosystemSimulation()

for generation in range(20):
    sim.run_generation()
    print("Generation:", generation)
