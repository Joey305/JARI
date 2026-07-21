#!/usr/bin/env python3
"""Small deterministic DockQ stand-in for pipeline smoke tests."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def scaled_value(label: str, left: Path, right: Path, minimum: float, maximum: float) -> float:
    digest = hashlib.sha256(f"{label}:{left.name}:{right.name}".encode("utf-8")).hexdigest()
    span = maximum - minimum
    raw = int(digest[:8], 16) / 0xFFFFFFFF
    return minimum + (raw * span)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: fake_dockq.py <native_pdb> <model_pdb>", file=sys.stderr)
        return 2

    native_pdb = Path(sys.argv[1])
    model_pdb = Path(sys.argv[2])

    dockq = scaled_value("dockq", native_pdb, model_pdb, 0.45, 0.95)
    irms = scaled_value("irms", native_pdb, model_pdb, 0.5, 4.5)
    lrms = scaled_value("lrms", native_pdb, model_pdb, 1.0, 8.0)

    print(f"DockQ {dockq:.3f}")
    print(f"iRMS {irms:.3f}")
    print(f"LRMS {lrms:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
