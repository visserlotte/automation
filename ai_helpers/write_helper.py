#!/usr/bin/env python3
import datetime as dt
import subprocess
from pathlib import Path

AI_EDIT_LOG = Path.home() / "automation" / "logs" / "self-edits.log"
AI_EDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


def write_helper(name, content):
    helper_path = Path.home() / "automation" / "helpers" / name
    helper_path.write_text(content)
    subprocess.run(["chmod", "+x", str(helper_path)], check=True)
    with AI_EDIT_LOG.open("a") as log:
        log.write(f"{dt.datetime.utcnow().isoformat()}  wrote {helper_path}\n")


if __name__ == "__main__":
    # demo (creates hello.sh)
    write_helper("hello.sh", "#!/usr/bin/env bash\necho Hello\n")
