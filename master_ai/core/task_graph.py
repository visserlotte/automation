from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

TaskFn = Callable[[], Any]


@dataclass
class Task:
    name: str
    run: TaskFn


@dataclass
class TaskGraph:
    tasks: list[Task] = field(default_factory=list)

    def add(self, name: str, fn: TaskFn) -> TaskGraph:
        self.tasks.append(Task(name, fn))
        return self

    def execute(self) -> None:
        for t in self.tasks:
            print(f"[Task] {t.name}…")
            t.run()
            print(f"[Task] {t.name} ✓")
