# Test du pipeline Supercluster (Niveau 5)
import sys
import os
import subprocess

def test_supercluster_pipeline():
    # Détecte la racine du projet (là où se trouve ce script)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    cwd = os.getcwd()
    if os.path.basename(cwd) != os.path.basename(project_root):
        print(f"[INFO] Changement de dossier courant pour la racine du projet : {project_root}")
        os.chdir(project_root)
    # Relance le test en mode module avec PYTHONPATH forcé
    cmd = [sys.executable, '-m', 'AI_HEDGE_FUND_SYSTEM.evolution_levels.level_5_supercluster.test_pipeline_supercluster']
    if 'test_pipeline_supercluster.py' in sys.argv[0]:
        # Empêche boucle infinie
        if os.environ.get('SUPERCLUSTER_TEST_RECURSION') == '1':
            print("[ERREUR] Boucle de relance détectée. Abandon.")
            sys.exit(2)
        env = os.environ.copy()
        env['SUPERCLUSTER_TEST_RECURSION'] = '1'
        # Ajoute le project_root au PYTHONPATH
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    # Sinon, exécution normale (import en tant que module)
    try:
        from . import pipeline_supercluster
        pipeline_supercluster.main()
        print("[TEST] test_pipeline_supercluster.py terminé avec succès.")
    except (ImportError, SystemError, ValueError):
        # Fallback: exécute le script pipeline_supercluster.py directement
        print("[INFO] Import en tant que module échoué, exécution directe du script pipeline_supercluster.py...")
        script_path = os.path.join(os.path.dirname(__file__), 'pipeline_supercluster.py')
        result = subprocess.run([sys.executable, script_path])
        if result.returncode == 0:
            print("[TEST] test_pipeline_supercluster.py terminé avec succès (mode script).")
        else:
            print("[ERREUR] L'exécution directe du pipeline a échoué.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    test_supercluster_pipeline()
