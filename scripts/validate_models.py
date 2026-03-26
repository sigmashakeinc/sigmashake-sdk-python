#!/usr/bin/env python3
"""Validate Python SDK models against the OpenAPI spec.

This is a convenience wrapper that delegates to the canonical drift detector
in sigmashake-openapi/scripts/.

Usage:
    python3 scripts/validate_models.py          # from SDK root
    python3 scripts/validate_models.py --json   # JSON output

Exit codes:
    0 = models match the OpenAPI spec
    1 = drift detected
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parent.parent
OPENAPI_ROOT = SDK_ROOT.parent / "sigmashake-openapi"
VALIDATOR = OPENAPI_ROOT / "scripts" / "validate_python_sdk.py"
SPEC = OPENAPI_ROOT / "openapi.yaml"
MODELS = SDK_ROOT / "src" / "sigmashake" / "models.py"


def main() -> int:
    if not VALIDATOR.exists():
        print(
            f"ERROR: Drift detector not found at {VALIDATOR}\n"
            "Make sure sigmashake-openapi is checked out as a sibling directory.",
            file=sys.stderr,
        )
        return 1

    args = [
        sys.executable,
        str(VALIDATOR),
        "--spec", str(SPEC),
        "--models", str(MODELS),
    ]
    if "--json" in sys.argv:
        args.append("--json")

    result = subprocess.run(args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
