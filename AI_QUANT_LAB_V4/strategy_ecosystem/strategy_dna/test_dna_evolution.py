import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dna_generator import generate_random_dna
from dna_mutation import mutate_dna
from dna_crossover import crossover
from dna_registry import DNARegistry
from dna_decoder import decode_dna

# Générer deux stratégies aléatoires
parent1 = generate_random_dna()
parent2 = generate_random_dna()
print("Parent 1:", decode_dna(parent1))
print("Parent 2:", decode_dna(parent2))

# Mutation
mutated = mutate_dna(parent1)
print("Mutated Parent 1:", decode_dna(mutated))

# Crossover
child = crossover(parent1, parent2)
print("Child (crossover):", decode_dna(child))

# Registry
registry = DNARegistry()
registry.add(parent1)
registry.add(parent2)
registry.add(child)
print("Population size:", len(registry.get_population()))
