import json
from pathlib import Path
from typing import List
from models import Task

DATA_FILE = Path.home() / ".smart_todo.json"


def load_tasks() -> List[Task]:
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return [Task.from_dict(t) for t in data]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def save_tasks(tasks: List[Task]) -> None:
    DATA_FILE.write_text(
        json.dumps([t.to_dict() for t in tasks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )