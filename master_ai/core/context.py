from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunContext:
    root: Path
    artifacts: Path
    run_id: str

    @classmethod
    def new(cls, root: Path) -> RunContext:
        run_id = time.strftime("%Y%m%d_%H%M%S")
        artifacts = root / "artifacts" / run_id
        artifacts.mkdir(parents=True, exist_ok=True)
        return cls(root=root, artifacts=artifacts, run_id=run_id)
