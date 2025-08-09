from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Job:
    name: str
    fn: Callable[[], Any]


class JobQueue:
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    def add(self, name: str, fn: Callable[[], Any]) -> JobQueue:
        self.jobs.append(Job(name, fn))
        return self

    def run(self) -> None:
        for j in self.jobs:
            print(f"[Queue] {j.name}…")
            j.fn()
            print(f"[Queue] {j.name} ✓")
