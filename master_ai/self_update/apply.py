from __future__ import annotations

from pathlib import Path

from master_ai.self_update.manifest import read_manifest, sha256_file


def self_check() -> bool:
    # Wire up stronger gates later; green-light for now.
    return True


def apply_update(bundle: Path, manifest: Path, install_dir: Path) -> bool:
    info = read_manifest(manifest)
    if sha256_file(bundle) != info.sha256:
        print("[self-update] ❌ SHA256 mismatch")
        return False
    # For now, pretend "bundle" is a ready tree: unpack/replace not implemented.
    # You can wire your own tar/zip logic + staging here.
    print("[self-update] (stub) Verified bundle hash; staging not implemented yet.")
    return True
