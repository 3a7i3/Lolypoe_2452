import subprocess
import sys
import os

# 1. Lancer la simulation évolutive
print("[1/4] Lancement de la simulation darwinienne...")
ret = subprocess.run([sys.executable, "run_strategy_factory.py"])
if ret.returncode != 0:
    print("Erreur lors de l'exécution de la simulation.")
    sys.exit(1)

# 2. Générer les visualisations avancées, analyse textuelle, GIF
print("[2/4] Génération des visualisations avancées et analyse...")
ret = subprocess.run([sys.executable, "results/visualize_population.py"])
if ret.returncode != 0:
    print("Erreur lors de la génération des visualisations.")
    sys.exit(1)

# 3. (Optionnel) Lancer le dashboard interactif si disponible
panel_script = os.path.join("results", "dashboard_panel.py")
if os.path.exists(panel_script):
    print("[3/4] Lancement du dashboard Panel...")
    subprocess.Popen([sys.executable, panel_script])
else:
    print("[3/4] Dashboard Panel non trouvé (optionnel)")

# 4. (Optionnel) Générer les vidéos MP4 à partir des GIF
try:
    import moviepy.editor as mpy
    for world in ["trend", "range", "crash", "chaos"]:
        gif_path = f"results/species_evolution_{world}.gif"
        mp4_path = f"results/species_evolution_{world}.mp4"
        if os.path.exists(gif_path):
            print(f"Conversion {gif_path} -> {mp4_path}")
            clip = mpy.VideoFileClip(gif_path)
            clip.write_videofile(mp4_path, fps=10)
except ImportError:
    print("moviepy non installé : conversion GIF->MP4 sautée.")

print("\nOrchestration complète terminée. Tout est prêt dans le dossier results !")
