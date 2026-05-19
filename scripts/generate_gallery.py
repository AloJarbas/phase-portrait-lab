#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from phaseportraitlab.brusselator_atlas import (
    default_brusselator_parameter_atlas,
    render_brusselator_parameter_atlas,
    write_brusselator_parameter_report,
)
from phaseportraitlab.brusselator_sweep import render_brusselator_hopf_sweep, sweep_brusselator_b_range, write_brusselator_hopf_report
from phaseportraitlab.chemistry_local_global import write_chemistry_local_global_report
from phaseportraitlab.chemistry_comparison import write_chemical_oscillator_comparison_report
from phaseportraitlab.chemistry_horizon_compare import (
    build_brusselator_horizon_rows,
    build_selkov_horizon_rows,
    export_png_from_svg,
    render_chemistry_horizon_compare_svg,
    write_chemistry_horizon_compare_report,
)
from phaseportraitlab.gallery import build_gallery
from phaseportraitlab.nonlinear_saddle import write_pendulum_nonlinear_saddle_packet
from phaseportraitlab.selkov_atlas import (
    default_selkov_parameter_atlas,
    render_selkov_parameter_atlas,
    write_selkov_parameter_report,
)


def main() -> None:
    assets = REPO / "assets"
    paths = build_gallery(assets)
    sweep_rows = sweep_brusselator_b_range()
    sweep_path = assets / "brusselator-hopf-sweep.svg"
    sweep_report_path = REPO / "reports" / "brusselator-hopf-sweep.md"
    render_brusselator_hopf_sweep(sweep_rows, output=sweep_path)
    write_brusselator_hopf_report(sweep_rows, sweep_report_path)
    paths.append(sweep_path)

    atlas_cells = default_brusselator_parameter_atlas()
    atlas_path = assets / "brusselator-parameter-atlas.svg"
    atlas_report_path = REPO / "reports" / "brusselator-parameter-atlas.md"
    render_brusselator_parameter_atlas(atlas_cells, output=atlas_path)
    write_brusselator_parameter_report(atlas_cells, atlas_report_path)
    paths.append(atlas_path)

    selkov_cells = default_selkov_parameter_atlas()
    selkov_path = assets / "selkov-parameter-atlas.svg"
    selkov_report_path = REPO / "reports" / "selkov-parameter-atlas.md"
    chemistry_report_path = REPO / "reports" / "chemical-oscillator-comparison.md"
    local_global_report_path = REPO / "reports" / "chemistry-local-to-global.md"
    horizon_svg_path = assets / "chemistry-horizon-convergence.svg"
    horizon_png_path = assets / "chemistry-horizon-convergence.png"
    horizon_csv_path = assets / "chemistry-horizon-convergence.csv"
    horizon_report_path = REPO / "reports" / "chemistry-horizon-convergence.md"
    render_selkov_parameter_atlas(selkov_cells, output=selkov_path)
    write_selkov_parameter_report(selkov_cells, selkov_report_path)
    write_chemical_oscillator_comparison_report(atlas_cells, selkov_cells, chemistry_report_path)
    write_chemistry_local_global_report(atlas_cells, selkov_cells, local_global_report_path)
    paths.append(selkov_path)

    brusselator_horizon_rows = build_brusselator_horizon_rows()
    selkov_horizon_rows = build_selkov_horizon_rows()
    render_chemistry_horizon_compare_svg(brusselator_horizon_rows, selkov_horizon_rows, output=horizon_svg_path)
    export_png_from_svg(horizon_svg_path, horizon_png_path)
    write_chemistry_horizon_compare_report(brusselator_horizon_rows, selkov_horizon_rows, horizon_report_path)
    with horizon_csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "model",
                "a",
                "b",
                "edge_distance",
                "short_settle_time",
                "short_sample_time",
                "short_x_amplitude",
                "short_period",
                "short_peak_count",
                "long_settle_time",
                "long_sample_time",
                "long_x_amplitude",
                "long_period",
                "long_peak_count",
            ]
        )
        for row in [*brusselator_horizon_rows, *selkov_horizon_rows]:
            writer.writerow(
                [
                    row.model,
                    f"{row.a:.6f}",
                    f"{row.b:.6f}",
                    f"{row.edge_distance:.6f}",
                    f"{row.short_settle_time:.2f}",
                    f"{row.short_sample_time:.2f}",
                    f"{row.short_x_amplitude:.8f}",
                    "" if row.short_period is None else f"{row.short_period:.8f}",
                    row.short_peak_count,
                    f"{row.long_settle_time:.2f}",
                    f"{row.long_sample_time:.2f}",
                    f"{row.long_x_amplitude:.8f}",
                    "" if row.long_period is None else f"{row.long_period:.8f}",
                    row.long_peak_count,
                ]
            )
    paths.append(horizon_svg_path)

    pendulum_paths = write_pendulum_nonlinear_saddle_packet(repo=REPO)
    for path in pendulum_paths:
        print(f"WROTE {path}")

    for path in paths:
        print(f"WROTE {path}")
    print(f"WROTE {sweep_report_path}")
    print(f"WROTE {atlas_report_path}")
    print(f"WROTE {selkov_report_path}")
    print(f"WROTE {chemistry_report_path}")
    print(f"WROTE {local_global_report_path}")
    print(f"WROTE {horizon_png_path}")
    print(f"WROTE {horizon_csv_path}")
    print(f"WROTE {horizon_report_path}")


if __name__ == "__main__":
    main()
