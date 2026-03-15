import os
import pandas as pd

class Storage:
    def __init__(self, base_dir="features_storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_csv(self, df, filename):
        path = os.path.join(self.base_dir, filename)
        df.to_csv(path, index=False)
