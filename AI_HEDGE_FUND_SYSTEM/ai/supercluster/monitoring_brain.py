import psutil

class MonitoringBrain:
    def report(self):
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        print(f"[MonitoringBrain] CPU usage: {cpu}% | Memory usage: {mem}%")
        # Extend: add node health, strategy perf, risk, alerts
        return {"cpu": cpu, "memory": mem}
