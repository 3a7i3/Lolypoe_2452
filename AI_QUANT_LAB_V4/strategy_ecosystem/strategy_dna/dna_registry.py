class DNARegistry:
    def __init__(self):
        self.population = []
    def add(self, dna):
        self.population.append(dna)
    def get_population(self):
        return self.population
