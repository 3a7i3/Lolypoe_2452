# Guide d’utilisation rapide – AI Quant Lab V4

## 1. Configuration
- Remplir `config/credentials.env` avec vos clés API, token Telegram, etc.
- Adapter les paramètres de slippage, frais, mode dans le .env ou via les arguments des bots.

## 2. Lancement
- Dashboard web : `streamlit run supervision/dashboard_web.py`
- API REST : `uvicorn supervision.dashboard_api:app --reload`
- Bot Telegram : `python supervision/telegram_bot.py`

## 3. Exemples
- Recevoir une alerte Telegram : déclencher une alerte via AlertManager
- Visualiser le portefeuille : ouvrir le dashboard web
- Exécuter un trade simulé : utiliser SniperBot en mode paper

### Exemple avancé : pipeline autonome complet

```python
from pipeline_autonome import run_pipeline
from supervision.dashboard_web import render_dashboard
from supervision.alert_manager import AlertManager

# Initialiser AlertManager et modules (voir pipeline_autonome.py)
alerts = AlertManager()
run_pipeline(iterations=5, mode="paper")

# Monitoring dashboard
strategies = [{"name": "Momentum", "score": 0.92}]
portfolio = {"total_capital": 100000, "allocations": {"Momentum": 50000}}
trades = [{"token": "TOKEN1", "type": "buy", "amount": 1000}]
render_dashboard(strategies, portfolio, trades, alerts.get_recent_alerts())
```

## 4. Tests
- Lancer tous les tests unitaires :
  ```sh
  cd crypto_quant_v16
  python -m unittest discover -s tests -p 'test_*.py'
  ```

## 5. Dépannage
- Vérifier les logs (AlertManager, dashboard, Telegram)
- S’assurer que les credentials sont valides
- Consulter les docstrings pour l’API de chaque module
