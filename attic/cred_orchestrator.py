import os, pathlib, re, subprocess, json, textwrap
from typing import Optional, Dict

ENV_PATH = pathlib.Path.home() / "automation" / ".env"

def mask(s: str, keep: int = 4) -> str:
    if not s: return ""
    return s[:keep] + "…" + s[-keep:] if len(s) > keep*2 else "…"

def _kv_from_text(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', line)
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
    return out

def _extract_block(text: str, header: str) -> Optional[str]:
    # Header like "CRED AWS", case-insensitive
    pat = re.compile(rf'^\[\s*{re.escape(header)}\s*\]\s*$', re.I | re.M)
    m = pat.search(text)
    if not m: return None
    start = m.end()
    # Scan until the next [CRED ...] or end
    tail = text[start:]
    m2 = re.search(r'^\s*\[CRED\b.*?\]\s*$', tail, re.I | re.M)
    block = tail[:m2.start()] if m2 else tail
    return block.strip()

def _aws_is_ready() -> bool:
    try:
        r = subprocess.run(["aws","sts","get-caller-identity"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except Exception:
        return False

def _write_env_updates(upd: Dict[str, str]) -> None:
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    existing = {}
    for i, ln in enumerate(lines):
        if "=" in ln and not ln.lstrip().startswith("#"):
            k = ln.split("=", 1)[0].strip()
            existing[k] = i
    for k, v in upd.items():
        entry = f"{k}={v}"
        if k in existing:
            lines[existing[k]] = entry
        else:
            lines.append(entry)
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(lines) + "\n")

def _apply_aws_keys(akid: str, secret: str, region: str, profile: str="default") -> str:
    # Persist with aws configure (safe and idempotent)
    subprocess.run(["aws","configure","set","aws_access_key_id", akid, "--profile", profile], check=True)
    subprocess.run(["aws","configure","set","aws_secret_access_key", secret, "--profile",_]()


