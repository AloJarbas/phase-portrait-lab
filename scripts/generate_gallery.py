#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from phaseportraitlab.brusselator_sweep import render_brusselator_hopf_sweep, sweep_brusselator_b_range, write_brusselator_hopf_report
from phaseportraitlab.gallery import build_gallery


def main() -> None:
    assets = REPO / "assets"
    paths = build_gallery(assets)
    sweep_rows = sweep_brusselator_b_range()
    sweep_path = assets / "brusselator-hopf-sweep.svg"
    report_path = REPO / "reports" / "brusselator-hopf-sweep.md"
    render_brusselator_hopf_sweep(sweep_rows, output=sweep_path)
    write_brusselator_hopf_report(sweep_rows, report_path)
    paths.append(sweep_path)
    for path in paths:
        print(f"WROTE {path}")
    print(f"WROTE {report_path}")


if __name__ == "__main__":
    main()
