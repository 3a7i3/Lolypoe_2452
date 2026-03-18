# PowerShell script: setup_quant_matrix_venv.ps1
# Crée un venv propre, installe toutes les dépendances, et lance la matrice

# 1. Créer l'environnement virtuel
python -m venv .venv

# 2. Activer le venv
.\.venv\Scripts\Activate.ps1

# 3. Mettre à jour pip, setuptools, wheel
python -m pip install --upgrade pip setuptools wheel

# 4. Installer les dépendances nécessaires
pip install pandas scikit-learn yfinance investpy

# 5. Lancer la matrice sur données réelles
python AI_HEDGE_FUND_SYSTEM/quant_matrix/run_quant_matrix.py
