# Dépannage – AI Quant Lab V4

## Problèmes courants
- **Erreur ImportError sur tests/** : vérifier la présence de `__init__.py` dans tests/
- **ModuleNotFoundError: dotenv** : installer avec `pip install python-dotenv`
- **Bot Telegram ne démarre pas** : vérifier TELEGRAM_TOKEN et TELEGRAM_CHAT_ID dans le .env
- **API REST inaccessible** : vérifier que FastAPI/uvicorn sont installés et le port utilisé
- **Aucune alerte reçue** : vérifier la config AlertManager et les logs

## Conseils
- Toujours consulter les logs pour diagnostiquer
- Utiliser les docstrings pour comprendre chaque module
- Tester chaque composant indépendamment avant intégration
