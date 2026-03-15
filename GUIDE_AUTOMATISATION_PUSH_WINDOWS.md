# Guide détaillé : Automatiser les pushes Git sous Windows

Ce guide explique comment automatiser les commits et pushes de votre dépôt local vers GitHub à l’aide d’un script PowerShell et du Planificateur de tâches Windows.

## 1. Pré-requis
- Git installé et accessible dans le PATH
- Accès au dépôt local cloné
- Script `push_with_message.ps1` présent dans le dossier du projet

## 2. Tester le script manuellement
Dans PowerShell, placez-vous dans le dossier du projet et lancez :

```powershell
./push_with_message.ps1 -Message "Auto: commit et push automatique"
```

Vérifiez que les changements sont bien poussés sur GitHub.

## 3. Créer une tâche planifiée
1. Ouvrez le **Planificateur de tâches Windows** (Task Scheduler)
2. Cliquez sur **Créer une tâche...**
3. Onglet **Général** :
   - Nommez la tâche (ex: "Push Git Auto")
   - Cochez "Exécuter avec les autorisations maximales"
4. Onglet **Déclencheurs** :
   - Cliquez sur **Nouveau...**
   - Choisissez la fréquence (ex: toutes les heures, à chaque ouverture de session, etc.)
5. Onglet **Actions** :
   - Cliquez sur **Nouveau...**
   - Action : "Démarrer un programme"
   - Programme/script : `powershell.exe`
   - Ajouter des arguments :
     ```
     -ExecutionPolicy Bypass -File "C:\Users\WINDOWS\crypto_ai_terminal\push_with_message.ps1" -Message "Auto: commit et push automatique"
     ```
   - Démarrer dans : `C:\Users\WINDOWS\crypto_ai_terminal`
6. Validez et testez la tâche.

## 4. Conseils
- Vérifiez que vos identifiants Git sont mémorisés (utilisez `git config credential.helper` ou SSH).
- Consultez l’historique des tâches dans le Planificateur pour diagnostiquer d’éventuelles erreurs.
- Personnalisez le message de commit si besoin.

## 5. Pour aller plus loin
- Ajoutez une notification (email, popup) en cas d’échec.
- Utilisez un fichier log pour tracer les pushes automatiques.

---

Pour toute question ou extension (détection de branche, logs, alertes), demandez-moi !
