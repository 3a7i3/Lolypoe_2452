from strategy_factory.alpha_vault import AlphaVault
import json
import matplotlib.pyplot as plt

# Simule un vault rempli (à remplacer par un vrai vault persistant)
vault = AlphaVault()

# Charger le vault depuis la dernière simulation massive
def load_vault_from_large_run():
    # On relance la simulation pour récupérer le vault en mémoire
    from run_strategy_factory_large import vault
    return vault

vault = load_vault_from_large_run()

# Export JSON
with open("alpha_vault_export.json", "w") as f:
    json.dump(vault.database, f, indent=2)
print(f"Exporté {len(vault.database)} stratégies dans alpha_vault_export.json")

# Visualisation des scores
scores = [entry["score"] for entry in vault.database]
plt.figure(figsize=(10,5))
plt.hist(scores, bins=30, color='skyblue', edgecolor='black')
plt.title("Distribution des scores des stratégies Alpha Vault")
plt.xlabel("Score")
plt.ylabel("Nombre de stratégies")
plt.tight_layout()
plt.savefig("alpha_vault_scores.png")
plt.show()
