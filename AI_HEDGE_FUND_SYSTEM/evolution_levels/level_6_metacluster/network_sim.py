# Niveau 6 — Simulateur réseau pour clusters
import random

class NetworkSim:
    def __init__(self, latency_range=(10, 100)):
        self.latency_range = latency_range  # ms

    def send(self, cluster_id, data):
        latency = random.randint(*self.latency_range)
        # Simule un délai réseau
        print(f"[NetworkSim] Envoi à cluster {cluster_id} (latence simulée: {latency} ms)")
        return latency, data
