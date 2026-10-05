from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Task:
    title: str
    done: bool = False
    due_at: Optional[str] = None
    reminded: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(**d)