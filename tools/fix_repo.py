import re
import sys
from pathlib import Path


def _insert_after_top_import_block(text: str, snippet: str) -> str:
    """Insert snippet right after the top import block (or prepend if none)."""
    pat = r"^(?:\s*(?:from [^\n]+|import [^\n]+)\n)+"
    m = re.search(pat, text, flags=re.MULTILINE)
    if m:
        return text[: m.end()] + snippet + text[m.end() :]
    return snippet + text


def _remove_all_chat_log_path_defs_blockwise(text: str) -> tuple[str, int]:
    """
    Remove every definition of chat_log_path by scanning line blocks.
    This is robust against different docstrings/indent/blank lines.
    """
    lines = text.splitlines(keepends=True)
    i = 0
    remove_ranges = []

    def is_indented(line: str) -> bool:
        return line.startswith((" ", "\t"))

    while i < len(lines):
        line = lines[i]
        if re.match(r"^[ \t]*def\s+chat_log_path\s*\(", line):
            start = i
            i += 1
            # Consume the function body: indented or blank lines
            while i < len(lines):
                if lines[i].strip() == "":
                    i += 1
                    continue
                if not is_indented(lines[i]):
                    break
                i += 1
            remove_ranges.append((start, i))
            continue
        i += 1

    if not remove_ranges:
        return text, 0

    # Remove from the end to preserve indices
    for start, end in reversed(remove_ranges):
        del lines[start:end]

    return "".join(lines), len(remove_ranges)


def rewrite_ai_utils():
    p = Path("ai_helpers/ai_utils.py")
    if not p.exists():
        print("[skip] ai_helpers/ai_utils.py not found")
        return
    s = p.read_text(encoding="utf-8")

    # 1) Remove broken lambda variant, if present.
    s = re.sub(r"(?m)^[ \t]*/\s*chat_log_path\s*=\s*\([\s\S]*?\)\s*$", "", s)

    # 2) Remove late 'from pathlib import Path' after STATUS HOOK (E402).
    s, removed = re.subn(
        r"\n# === STATUS HOOK ===\s*\nfrom pathlib import Path",
        "\n# === STATUS HOOK ===",
        s,
        flags=re.MULTILINE,
    )
    if removed:
        print("[fix] moved late 'from pathlib import Path' to top")

    # 3) Remove ALL existing chat_log_path() defs (blockwise, robust).
    s, count = _remove_all_chat_log_path_defs_blockwise(s)
    if count:
        print(f"[fix] removed {count} prior chat_log_path() definition(s)")

    # 4) Ensure required imports near the top.
    if "import pathlib" not in s[:2000]:
        s = _insert_after_top_import_block(s, "import pathlib\n")
        print("[fix] ensured 'import pathlib' at top")
    if "from pathlib import Path" not in s[:2000]:
        s = _insert_after_top_import_block(s, "from pathlib import Path\n")
        print("[fix] ensured 'from pathlib import Path' at top")

    # 5) Insert canonical chat_log_path() once.
    canonical = (
        "\n"
        "def chat_log_path(project: str) -> pathlib.Path:\n"
        '    """Return ~/automation/projects/<project>/chat_history.json."""\n'
        "    return (\n"
        "        pathlib.Path.home()\n"
        '        / "automation"\n'
        '        / "projects"\n'
        "        / project\n"
        '        / "chat_history.json"\n'
        "    )\n"
    )
    # Always insert our canonical one after top imports (since we just removed all)
    s = _insert_after_top_import_block(s, canonical)
    print("[fix] inserted canonical chat_log_path()")

    # 6) Wrap the long f-string status line, if present.
    s = re.sub(
        r'(?m)^\s*return\s+f"Latest micro-project: .*?%H:%M\}\)"\s*$',
        (
            "        return (\n"
            '            f"Latest micro-project: {plans[0].name} "\n'
            '            f"(edited {plans[0].stat().st_mtime:%Y-%m-%d %H:%M})"\n'
            "        )"
        ),
        s,
    )

    p.write_text(s, encoding="utf-8")
    print("[fix] ai_utils normalized")


def rewrite_master_ai_config():
    p = Path("ai_helpers/master_ai_config.py")
    if not p.exists():
        print("[skip] ai_helpers/master_ai_config.py not found")
        return
    s = p.read_text(encoding="utf-8")

    # Put `import openai` into the top import block.
    s = re.sub(r"(?m)^\s*import openai\s*$", "", s)
    s = _insert_after_top_import_block(s, "import openai\n")

    # Ensure api_key assignment exists (assumes OPENAI_API_KEY defined in the file).
    if "openai.api_key = OPENAI_API_KEY" not in s:
        s += "\nopenai.api_key = OPENAI_API_KEY\n"

    p.write_text(s, encoding="utf-8")
    print("[fix] master_ai_config normalized")


def rewrite_planner():
    p = Path("master_ai/agents/planner.py")
    if not p.exists():
        print("[skip] master_ai/agents/planner.py not found")
        return
    s = p.read_text(encoding="utf-8")

    # Outside an `except`, there is no `e`; use `from None` to satisfy B904.
    s = s.replace(
        'raise ValueError("taskfile: not valid JSON (and not YAML by extension)") from e',
        ('raise ValueError("taskfile: not valid JSON (and not YAML by extension)") from None'),
    )

    p.write_text(s, encoding="utf-8")
    print("[fix] planner normalized")


def main():
    for fn in (rewrite_ai_utils, rewrite_master_ai_config, rewrite_planner):
        try:
            fn()
        except Exception as exc:
            print(f"[error] {fn.__name__}: {exc}", file=sys.stderr)
    print("fixers applied")


if __name__ == "__main__":
    main()
