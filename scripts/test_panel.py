import os
import panel as pn

# Créer un dossier dans data/
dossier = "data/test_dossier"
os.makedirs(dossier, exist_ok=True)

# Afficher un sujet sur Panel
pn.extension()

pn.Column(
    "# 🚀 Crypto AI Terminal",
    f"Dossier créé : {dossier}",
    "Sujet : Analyse des cryptomonnaies avec IA"
).servable()