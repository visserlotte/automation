from __future__ import annotations

import time
from pathlib import Path

import requests

# Optional event logging: if runtime.events.log isn't available, no-op.
try:
    from .events import log as _emit
except Exception:  # pragma: no cover

    def _emit(*_a, **_k):  # noqa: D401 - tiny shim
        pass


UA = "MasterAI/0.1 (+https://example.invalid)"


def _get(url: str, *, stream: bool = False, timeout: int = 30) -> requests.Response:
    return requests.get(url, headers={"User-Agent": UA}, stream=stream, timeout=timeout)


def fetch_file(
    url: str, dest: Path, retries: int = 3, backoff: float = 0.6, timeout: int = 30
) -> Path:
    """Download URL to dest with simple retry + backoff."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for i in range(1, retries + 1):
        try:
            _emit("log", {"step": 1, "line": f"download try {i}/{retries}: {url}"})
            with _get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            _emit("log", {"step": 1, "line": f"saved -> {dest}"})
            return dest
        except Exception as e:  # noqa: BLE001
            last_err = e
            _emit("log", {"step": 1, "line": f"download error: {e}"})
            if i < retries:
                time.sleep(backoff * i)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def fetch_text(url: str, timeout: int = 30) -> str:
    r = _get(url, stream=False, timeout=timeout)
    r.raise_for_status()
    return r.text
