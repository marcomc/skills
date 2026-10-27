#!/usr/bin/env python3
"""Compatibility entrypoint; the neutral review coordinator owns implementation."""

import runpy
from pathlib import Path

_here = Path(__file__).resolve()
_candidates = (
    _here.parents[2] / "review-coordinator" / "scripts" / _here.name,
    _here.parents[3] / "quality-review" / "review-coordinator" / "scripts" / _here.name,
)
_target = next((p for p in _candidates if p.is_file()), None)
if _target is None:
    raise SystemExit(
        "Install review-coordinator alongside this skill before using this command."
    )
_exports = runpy.run_path(str(_target))
globals().update({k: v for k, v in _exports.items() if not k.startswith("__")})

if __name__ == "__main__":
    raise SystemExit(_exports["main"]())
