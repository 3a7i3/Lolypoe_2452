from queue import Queue
from typing import Any, Dict, Optional


task_queue: "Queue[Dict[str, Any]]" = Queue()


def add_task(task: Dict[str, Any]) -> None:
    task_queue.put(task)


def get_task() -> Optional[Dict[str, Any]]:
    if not task_queue.empty():
        return task_queue.get()
    return None


def task_count() -> int:
    return task_queue.qsize()
