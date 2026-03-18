# Niveau 5 — ResearchNode

import threading
import random

class ResearchNode(threading.Thread):
    def __init__(self, node_id, task_queue, result_queue):
        super().__init__()
        self.node_id = node_id
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        while not self.task_queue.empty():
            try:
                task = self.task_queue.get_nowait()
            except Exception:
                break
            # Simulate strategy evaluation
            result = self.evaluate_strategy(task)
            self.result_queue.put((self.node_id, task, result))

    def evaluate_strategy(self, strategy):
        # Simulate evaluation (random score)
        return random.uniform(0, 1)
