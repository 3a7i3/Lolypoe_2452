import threading
import time
from typing import Callable, Dict, Any

from distributed.task_queue import get_task


class Worker:
    def __init__(self, name: str, handlers: Dict[str, Callable[[Dict[str, Any]], Any]]):
        self.name = name
        self.handlers = handlers
        self._running = False

    def run(self, poll_interval: float = 0.25) -> None:
        self._running = True
        while self._running:
            task = get_task()
            if task:
                task_type = task.get("type", "unknown")
                handler = self.handlers.get(task_type)
                if handler is not None:
                    result = handler(task)
                    response_queue = task.get("response_queue")
                    if response_queue is not None:
                        response_queue.put(
                            {
                                "task_id": task.get("task_id"),
                                "task_type": task_type,
                                "result": result,
                            }
                        )
                    print(f"{self.name} processed {task_type} (task_id={task.get('task_id')})")
                else:
                    print(f"{self.name} no handler for task type: {task_type}")
            time.sleep(poll_interval)

    def stop(self) -> None:
        self._running = False


def start_worker_thread(worker: Worker) -> threading.Thread:
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    return thread
