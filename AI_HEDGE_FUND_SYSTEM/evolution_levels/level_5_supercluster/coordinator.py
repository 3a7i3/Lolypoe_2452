# Niveau 5 — Coordinator

import threading
from queue import Queue
try:
    from .research_node import ResearchNode
except (ImportError, SystemError, ValueError):
    from research_node import ResearchNode

class Coordinator:
    def __init__(self, num_nodes=3):
        self.num_nodes = num_nodes
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.nodes = [ResearchNode(node_id=i, task_queue=self.task_queue, result_queue=self.result_queue) for i in range(num_nodes)]

    def distribute_tasks(self, tasks):
        for task in tasks:
            self.task_queue.put(task)
        for node in self.nodes:
            node.start()

    def collect_results(self):
        results = []
        while not self.result_queue.empty():
            result = self.result_queue.get()
            results.append(result)
        return results

    def run_cluster(self, tasks):
        self.distribute_tasks(tasks)
        for node in self.nodes:
            node.join()
        return self.collect_results()
