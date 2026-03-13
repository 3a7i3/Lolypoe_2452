# Trading Bot v3

Architecture de bot de trading crypto modulaire et extensible.

## Structure

- `main.py` – Classe principale du bot
- `config.py` – Configuration centralisée
- `core/` – Modules de logique métier
  - `market_data.py` – Accès aux données de marché (CCXT)
  - `indicators.py` – Calcul des indicateurs techniques
  - `strategy.py` – Logique de génération de signaux
  - `risk_management.py` – Gestion du risque
  - `logger.py` – Logging centralisé
- `interface/` – Dashboard Panel
  - `dashboard.py` – Interface interactive
- `data/` – Stockage des données
  - `trades.csv` – Historique des trades

## Lancer le dashboard

```powershell
cd bot-v3
python -m panel serve interface/dashboard.py --show
```

## Lancer le bot

```powershell
python main.py
```
