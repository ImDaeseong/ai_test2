"""Run the complete secret-free verification boundary for both local projects."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
MARKETING = REPOSITORY / "marketing_command_center"
THREADS = ROOT / "threads"
THREADS_CLIENT = THREADS / "examples" / "threads_python"


def verification_commands() -> list[tuple[str, list[str], Path]]:
    """Return the ordered offline gates with explicit executables and working directories."""
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm") or "npm"
    powershell = shutil.which("powershell.exe") or "powershell"
    python = sys.executable
    return [
        ("contract", [python, "sync_marketing_contract.py", "--check"], ROOT),
        ("community tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT),
        ("threads tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], THREADS),
        ("threads client tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], THREADS_CLIENT),
        ("marketing JavaScript tests", [npm, "test"], MARKETING),
        ("marketing Python tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], MARKETING),
        ("marketing validation", [npm, "run", "validate"], MARKETING),
        ("marketing lifecycle", [python, "scripts/smoke_lifecycle.py"], MARKETING),
        ("marketing browser E2E", [npm, "run", "e2e"], MARKETING),
        ("marketing Windows launcher", [powershell, "-ExecutionPolicy", "Bypass", "-File", "scripts/smoke_launcher.ps1"], MARKETING),
        ("repository tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], REPOSITORY),
        ("security hotspots", [python, "scripts/check_security_hotspots.py", "."], REPOSITORY),
        ("source-only boundary", [python, "scripts/check_source_only.py"], REPOSITORY),
    ]


def run_all(run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> int:
    """Run every gate in order and stop with the failing gate's exit code."""
    for name, command, cwd in verification_commands():
        print(f"\n=== {name} ===", flush=True)
        result = run(command, cwd=cwd, text=True, check=False)
        if result.returncode:
            print(f"FAIL: {name} (exit {result.returncode})", file=sys.stderr)
            return result.returncode
    print("\nPASS: all offline community integration gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
