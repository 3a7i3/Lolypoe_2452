param(
    [string]$Message = "Auto: sync local changes"
)

# Ajoute tous les changements
 git add .

# Commit avec message personnalisé
 git commit -m "$Message"

# Push sur la branche principale (main)
 git push origin main
