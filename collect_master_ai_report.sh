#!/usr/bin/env bash
set -euo pipefail

OUTDIR="/tmp/master_ai_report_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR" "$OUTDIR/logs" "$OUTDIR/src"
LOG="$OUTDIR/quick_summary.txt"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

log "Collecting Master-AI report into $OUTDIR"

# System
{
  echo "==== SYSTEM ===="; uname -a || true
  echo; echo "==== OS ===="; (lsb_release -a 2>/dev/null || cat /etc/os-release 2>/dev/null || true)
  echo; echo "==== PATH ===="; printf "%s\n" "$PATH"
  echo; echo "==== SHELL ===="; printf "%s\n" "$SHELL"
  echo; echo "==== WHOAMI ===="; whoami
  echo; echo "==== TIME ===="; date -Is
} > "$OUTDIR/system.txt"

# Python/tooling
{
  echo "==== PYTHON ===="; command -v python3 || true; python3 -V || true
  echo; echo "==== VENV DETECTION ===="; if [ -d ".venv" ]; then echo "Found .venv"; PY=".venv/bin/python"; else echo "No .venv; using system python3"; PY="python3"; fi
  echo "PY=$PY"
  echo; echo "==== PIP LIST ===="; "$PY" -m pip list 2>&1 || true
  echo; echo "==== LINT/TEST TOOLS ===="; (ruff --version 2>/dev/null || echo "ruff: not installed"); (mypy --version 2>/dev/null || echo "mypy: not installed"); (pytest --version 2>/dev/null || echo "pytest: not installed")
} > "$OUTDIR/python_tooling.txt"

# Git metadata only
{
  echo "==== GIT REMOTES ===="; git remote -v 2>/dev/null || true
  echo; echo "==== GIT STATUS ===="; git status -sb 2>/dev/null || true
  echo; echo "==== LAST 10 COMMITS ===="; git --no-pager log --oneline -n 10 2>/dev/null || true
  echo; echo "==== .gitignore ===="; [ -f .gitignore ] && sed -n '1,200p' .gitignore || echo "no .gitignore"
} > "$OUTDIR/git_state.txt"

# Layout
log "Indexing repository..."
{
  echo "==== TREE (depth 3) ===="
  if command -v tree >/dev/null 2>&1; then
    tree -L 3 -a -I ".git|__pycache__|.mypy_cache|.pytest_cache|.ruff_cache|.venv|node_modules"
  else
    find . -maxdepth 3 -not -path "./.git*" -not -path "./.venv*" -not -path "*/__pycache__/*" | sort
  fi
} > "$OUTDIR/layout.txt"

# Copy important source files (safe)
copy(){ [ -f "$1" ] && { mkdir -p "$OUTDIR/src/$(dirname "$1")"; cp "$1" "$OUTDIR/src/$1"; }; }
for f in master_ai.py pyproject.toml requirements.txt requirements-dev.txt Makefile README.md; do copy "$f"; done
for f in streamlit_chat.py ui/streamlit_chat.py; do copy "$f"; done
for f in self_update/manifest.py self_update/apply.py versions.json; do copy "$f"; done
# Package modules (best-effort)
for p in master_ai ai_helpers; do
  [ -d "$p" ] || continue
  find "$p" -type f -name "*.py" -print0 | xargs -0 -I{} sh -c 'mkdir -p "$OUTDIR/src/$(dirname "{}")"; cp "{}" "$OUTDIR/src/{}"'
done

# Logs (tails only)
if [ -d logs ]; then
  find logs -maxdepth 1 -type f -name "*.log" | while read -r f; do base=$(basename "$f"); tail -n 400 "$f" > "$OUTDIR/logs/${base%.log}.tail.log" || true; done
  [ -L logs/current_run.log ] && readlink -f logs/current_run.log > "$OUTDIR/logs/current_run.log.target" || true
fi

# Env (SAFE: names + lengths; .env keys only)
{
  echo "==== ENV VARS (names + value length only) ===="; env | LC_ALL=C sort | awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{name=$1; val=$0; sub(/^[^=]*=/,"",val); print name"=(len="length(val)")"}'
  echo; echo "==== .env (keys only) ===="; if [ -f .env ]; then awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{print $1"=***REDACTED***"} !/^[A-Za-z_][A-Za-z0-9_]*=/' .env | sed -n '1,200p'; else echo "no .env"; fi
} > "$OUTDIR/env_sanitized.txt"

# Static syntax check
{
  echo "==== PYTHON SYNTAX CHECK (selected) ====";
  find . -name "*.py" -not -path "./.venv/*" -not -path "./.git/*" -print0 | xargs -0 -I{} bash -c 'python3 -m py_compile "{}"' \
    && echo "OK: py_compile" || echo "py_compile: some files failed (fine—send report)"
} > "$OUTDIR/static_checks.txt"

# Zip/tar
ZIP="$OUTDIR.zip"
if command -v zip >/dev/null 2>&1; then
  ( cd "$(dirname "$OUTDIR")" && zip -r "$(basename "$ZIP")" "$(basename "$OUTDIR")" >/dev/null )
  ARCH="$ZIP"
else
  TAR="$OUTDIR.tgz"
  ( cd "$(dirname "$OUTDIR")" && tar czf "$(basename "$TAR")" "$(basename "$OUTDIR")" )
  ARCH="$TAR"
fi

log "Done."
log "ARCHIVE: $ARCH"
log "Upload or attach that archive here. Also paste $LOG for quick triage."
