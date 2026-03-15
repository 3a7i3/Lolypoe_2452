from dna_generator import generate_random_dna
from dna_registry import DNARegistry
from dna_selection import score_dna, select_best
from dna_decoder import decode_dna

# Générer une population de 10 stratégies
registry = DNARegistry()
for _ in range(10):
    registry.add(generate_random_dna())

population = registry.get_population()

# Scoring
for dna in population:
    print(decode_dna(dna), "score:", round(score_dna(dna), 3))

# Sélection naturelle : top 3
best = select_best(population, top_n=3)
print("\nTop 3 strategies:")
for dna in best:
    print(decode_dna(dna))
