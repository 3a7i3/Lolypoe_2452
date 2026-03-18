import json

class AlphaVaultPersistence:
    def __init__(self, path="alpha_vault.json"):
        self.path = path

    def save(self, vault_dict):
        with open(self.path, "w") as f:
            json.dump(vault_dict, f, indent=2)
        print(f"[Persistence] AlphaVault saved to {self.path}")

    def load(self):
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            print(f"[Persistence] AlphaVault loaded from {self.path}")
            return data
        except FileNotFoundError:
            print(f"[Persistence] No vault file found at {self.path}, starting fresh.")
            return {}
