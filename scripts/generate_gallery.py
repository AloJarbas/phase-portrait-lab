#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from phaseportraitlab.gallery import build_gallery


def main() -> None:
    assets = REPO / "assets"
    paths = build_gallery(assets)
    for path in paths:
        print(f"WROTE {path}")


if __name__ == "__main__":
    main()
