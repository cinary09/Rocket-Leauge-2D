from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def ensure_dependencies() -> None:
    """Install pygame-ce on first run when the pygame module is missing."""
    if importlib.util.find_spec("pygame") is not None:
        return

    root = Path(__file__).resolve().parent.parent
    requirements = root / "requirements.txt"
    print("pygame-ce is not installed. Installing project dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
    )
