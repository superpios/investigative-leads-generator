#!/usr/bin/env python3
"""
generate_leads.py - Wrapper che chiama apply_rules.py.

Mantiene la stessa interfaccia e gli stessi vincoli.

"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    cmd = [
        sys.executable,
        str(root / "scripts" / "apply_rules.py"),
        "--input", str(root / "data" / "input"),
        "--output", str(root / "data" / "leads"),
        "--rules", str(root / "rules" / "rules_v0.1.yaml"),
    ]

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
