import threading
from datetime import datetime
from typing import Callable, List, Set

from plyer import notification
from models import Task


class ReminderService:
    def __init__(
        self,
        get_tasks: Callable[[], List[Task]],
        save_tasks: Callable[[List[Task]], None],
        on_remind: Callable[[Task], None],
        interval_seconds: int = 30,
    ):
        self._get_tasks = get_tasks
        self._save_tasks = save_tasks
        self._on_remind = on_remind
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._notified_ids: Set[str] = set()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._check()
            self._stop.wait(self._interval)

    def _check(self) -> None:
        now = datetime.now()
        tasks = self._get_tasks()
        fired = False

        for task in tasks:
            if task.id in self._notified_ids:
                continue
            if task.done or task.reminded or not task.due_at:
                continue

            try:
                due = datetime.strptime(task.due_at, "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            if due <= now:
                self._notified_ids.add(task.id)
                task.reminded = True
                fired = True
                try:
                    notification.notify(
                        title="Promemoria",
                        message=task.title,
                        timeout=10,
                    )
                except Exception:
                    pass
                self._on_remind(task)

        if fired:
            try:
                self._save_tasks(tasks)
            except Exception:
                pass