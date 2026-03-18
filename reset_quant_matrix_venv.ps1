# PowerShell script: reset_quant_matrix_venv.ps1
# Supprime le venv, le recrée, installe toutes les dépendances, et lance la matrice

# 1. Supprimer l'ancien venv s'il existe
if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }

# 2. Créer un nouvel environnement virtuel
python -m venv .venv

# 3. Activer le venv
.\.venv\Scripts\Activate.ps1

# 4. Mettre à jour pip, setuptools, wheel
python -m pip install --upgrade pip setuptools wheel

# 5. Installer les dépendances nécessaires
pip install pandas scikit-learn yfinance investpy

# 6. Vérifier pkg_resources
python -c "import pkg_resources; print(pkg_resources.__file__)"

# 7. Lancer la matrice sur données réelles
python AI_HEDGE_FUND_SYSTEM/quant_matrix/run_quant_matrix.py
