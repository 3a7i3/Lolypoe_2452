import numpy as np

class AlphaGenerator:
    def create_signal(self, feature):
        signal = np.sign(feature)
        return signal
