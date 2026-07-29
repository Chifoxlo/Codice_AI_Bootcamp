#!/usr/bin/env python3
"""Verify that every decode_pedal_position(raw) result matches the DBC formula.

Exit codes
----------
0   All values match (raw * factor + offset) within floating-point tolerance.
1   At least one mismatch detected — implementation diverges from DBC.
"""

import json
import os
import sys

# Ensure the repo root is on the import path regardless of cwd.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from src.can.signal_decode import decode_pedal_position  # noqa: E402


def load_dbc(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    dbc_path = os.path.join(_REPO_ROOT, "signals.dbc.json")
    dbc = load_dbc(dbc_path)
    sig = dbc["messages"]["0x18F"]["signals"]["PedalPosition"]
    factor: float = sig["factor"]
    offset: float = sig["offset"]

    errors: list[str] = []
    for raw in range(256):
        expected = raw * factor + offset
        actual = decode_pedal_position(raw)
        if abs(actual - expected) > 1e-9:
            errors.append(
                f"  raw={raw:3d}: expected {expected:.6f}, got {actual:.6f}"
            )

    if errors:
        print("check_conversion: FAIL — decode does not match DBC:")
        for e in errors:
            print(e)
        return 1

    print(
        f"check_conversion: OK — all 256 raw values match "
        f"(factor={factor}, offset={offset})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
