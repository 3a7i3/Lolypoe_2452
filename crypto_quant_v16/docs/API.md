# Documentation API – AI Quant Lab V4

## Endpoints principaux (dashboard_api.py)

- `GET /status` : Statut du système
- `GET /alerts?n=10` : Dernières alertes (n)
- `GET /portfolio` : État du portefeuille
- `GET /strategies` : Stratégies actives
- `GET /trades?n=10` : Derniers trades

## Exemple de requête
```sh
curl http://localhost:8000/alerts?n=5
```

## Extension possible
- Ajouter endpoints pour actions (ex: POST /trade)
- Authentification (token, OAuth)
- Webhooks pour alertes externes
