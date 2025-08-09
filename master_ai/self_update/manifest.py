from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VersionInfo:
    version: str
    sha256: str
    url: str | None = None


def read_manifest(p: Path) -> VersionInfo:
    data = json.loads(p.read_text())
    return VersionInfo(**data)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
