class AlphaRegistry:
    def __init__(self):
        self.alphas = {}
    def register(self, name, score):
        self.alphas[name] = score
    def best(self):
        return sorted(
            self.alphas.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
