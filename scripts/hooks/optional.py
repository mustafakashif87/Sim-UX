"""Run a tool if it is installed; otherwise warn and exit 0.

Used by lefthook.yml so hooks behave the same on macOS, Linux and Windows
without shell syntax. CI is the hard gate, so a missing tool only skips.

Usage: python scripts/hooks/optional.py <tool> [args...]
"""

import shutil
import subprocess
import sys


def main() -> int:
    tool, *args = sys.argv[1:]
    if shutil.which(tool) is None:
        print(f"warning: {tool} not found; activate .venv. Skipping, CI will check.")
        return 0
    return subprocess.run([tool, *args]).returncode


if __name__ == "__main__":
    sys.exit(main())
