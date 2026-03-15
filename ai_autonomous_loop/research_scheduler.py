import time

class ResearchScheduler:
    def __init__(self, loop, interval_seconds=3600):
        self.loop = loop
        self.interval_seconds = interval_seconds

    def start(self):
        while True:
            print("Running research cycle...")
            self.loop.run_cycle()
            time.sleep(self.interval_seconds)
