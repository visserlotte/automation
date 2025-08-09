from __future__ import annotations

import shutil
from pathlib import Path


def stage_output(artifact_dir: Path, project_path: Path) -> Path:
    out = artifact_dir / "output"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(project_path, out)
    return out
