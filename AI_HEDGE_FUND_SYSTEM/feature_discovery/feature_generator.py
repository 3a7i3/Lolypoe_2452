import random

class FeatureGenerator:
    operations = ["add", "sub", "mul", "div"]
    def combine(self, f1, f2, op):
        if op == "add":
            return f1 + f2
        if op == "sub":
            return f1 - f2
        if op == "mul":
            return f1 * f2
        if op == "div":
            return f1 / (f2 + 1e-9)
