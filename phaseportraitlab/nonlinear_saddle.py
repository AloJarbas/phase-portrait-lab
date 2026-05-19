from __future__ import annotations

from dataclasses import dataclass
from html import escape
import math
from pathlib import Path
import shutil
import subprocess
from typing import Sequence

from .analysis import trajectories, vector_field
from .chemistry_horizon_compare import export_png_from_svg
from .systems import get_system


@dataclass(frozen=True)
class PendulumSeparatrixRow:
    shift: float
    exact_omega: float
    linear_omega: float

    @property
    def abs_error(self) -> float:
        return abs(self.linear_omega - self.exact_omega)


def pendulum_energy(theta: float, omega: float) -> float:
    return 0.5 * omega * omega + 1.0 - math.cos(theta)


def pendulum_separatrix_omega(shift: float) -> float:
    if not (0.0 <= shift <= math.pi):
        raise ValueError("shift must lie in [0, pi]")
    return 2.0 * math.sin(0.5 * shift)


def build_pendulum_separatrix_rows(*, samples: int = 181) -> list[PendulumSeparatrixRow]:
    if samples < 2:
        raise ValueError("samples must be at least 2")
    rows: list[PendulumSeparatrixRow] = []
    for index in range(samples):
        shift = math.pi * index / (samples - 1)
        rows.append(
            PendulumSeparatrixRow(
                shift=shift,
                exact_omega=pendulum_separatrix_omega(shift),
                linear_omega=shift,
            )
        )
    return rows


def _text(x: float, y: float, content: str, *, size: int = 16, fill: str = "#dce7f3", anchor: str = "start", weight: str = "normal") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" text-anchor="{anchor}" font-family="Helvetica, Arial, sans-serif" font-weight="{weight}">{escape(content)}</text>'


def _paragraph(
    x: float,
    y: float,
    content: str,
    *,
    size: int = 14,
    fill: str = "#dce7f3",
    width_chars: int = 44,
    line_height: float = 20.0,
    weight: str = "normal",
) -> str:
    import textwrap

    lines = textwrap.wrap(content, width=width_chars) or [content]
    tspans = [f'<tspan x="{x:.1f}" dy="0">{escape(lines[0])}</tspan>']
    tspans.extend(f'<tspan x="{x:.1f}" dy="{line_height:.1f}">{escape(line)}</tspan>' for line in lines[1:])
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-weight="{weight}">{"".join(tspans)}</text>'


def _line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#31465d", width: float = 1.0, dash: str | None = None, opacity: float = 1.0) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width:.1f}" opacity="{opacity:.2f}"{dash_attr}/>'


def _polyline(points: Sequence[tuple[float, float]], *, stroke: str, width: float = 3.0, opacity: float = 1.0) -> str:
    payload = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline fill="none" stroke="{stroke}" stroke-width="{width:.1f}" stroke-opacity="{opacity:.2f}" stroke-linejoin="round" stroke-linecap="round" points="{payload}"/>'


def _circle(x: float, y: float, *, r: float = 4.0, fill: str = "#f97316") -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'


def render_pendulum_nonlinear_saddle_svg(
    rows: Sequence[PendulumSeparatrixRow],
    *,
    output: str | Path,
    title: str = "Pendulum saddle: exact separatrix vs linear tangent",
) -> None:
    if not rows:
        raise ValueError("rows must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    system = get_system("simple-pendulum")
    field = vector_field(system, nx=15, ny=11)
    curves = trajectories(system, dt=0.03, steps=1400)

    width = 1560
    height = 900
    full_panel = (70.0, 150.0, 900.0, 790.0)
    local_panel = (950.0, 150.0, 1490.0, 790.0)

    def map_box(x: float, y: float, *, box: tuple[float, float, float, float], x_range: tuple[float, float], y_range: tuple[float, float]) -> tuple[float, float]:
        left, top, right, bottom = box
        xp = left + (x - x_range[0]) / (x_range[1] - x_range[0]) * (right - left)
        yp = bottom - (y - y_range[0]) / (y_range[1] - y_range[0]) * (bottom - top)
        return xp, yp

    def draw_axes(*, box: tuple[float, float, float, float], x_ticks: Sequence[tuple[float, str]], y_ticks: Sequence[tuple[float, str]], x_range: tuple[float, float], y_range: tuple[float, float], x_label: str, y_label: str) -> list[str]:
        left, top, right, bottom = box
        parts: list[str] = []
        for value, label in x_ticks:
            xp, _ = map_box(value, y_range[0], box=box, x_range=x_range, y_range=y_range)
            parts.append(_line(xp, top, xp, bottom, stroke="#24384b", dash="5 7"))
            parts.append(_text(xp, bottom + 24.0, label, size=12, fill="#9fb3c8", anchor="middle"))
        for value, label in y_ticks:
            _, yp = map_box(x_range[0], value, box=box, x_range=x_range, y_range=y_range)
            parts.append(_line(left, yp, right, yp, stroke="#24384b", dash="5 7"))
            parts.append(_text(left - 10.0, yp + 4.0, label, size=12, fill="#9fb3c8", anchor="end"))
        parts.append(_line(left, bottom, right, bottom, stroke="#8aa3bc", width=2.0))
        parts.append(_line(left, top, left, bottom, stroke="#8aa3bc", width=2.0))
        parts.append(_text((left + right) / 2.0, bottom + 50.0, x_label, size=14, anchor="middle"))
        parts.append(_text(left - 36.0, (top + bottom) / 2.0, y_label, size=14, anchor="middle",))
        return parts

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        _text(160.0, 60.0, title, size=34, weight="700"),
        _text(160.0, 92.0, "The upright pendulum is still a saddle, but its invariant set is an energy contour, not a pair of straight global eigenlines.", size=16, fill="#bfd0de"),
        f'<rect x="{full_panel[0]:.1f}" y="{full_panel[1]:.1f}" width="{full_panel[2]-full_panel[0]:.1f}" height="{full_panel[3]-full_panel[1]:.1f}" rx="22" fill="#122131" stroke="#58708c" stroke-width="1.8"/>',
        f'<rect x="{local_panel[0]:.1f}" y="{local_panel[1]:.1f}" width="{local_panel[2]-local_panel[0]:.1f}" height="{local_panel[3]-local_panel[1]:.1f}" rx="22" fill="#122131" stroke="#58708c" stroke-width="1.8"/>',
        _text(full_panel[0] + 20.0, full_panel[1] + 32.0, "Full pendulum portrait with the exact separatrix", size=22, weight="700"),
        _text(full_panel[0] + 20.0, full_panel[1] + 58.0, "Closed oscillations sit below the energy barrier. The orange curve is the barrier itself.", size=13, fill="#9fb3c8"),
        _text(local_panel[0] + 20.0, local_panel[1] + 32.0, "Top-saddle zoom", size=22, weight="700"),
        _paragraph(local_panel[0] + 20.0, local_panel[1] + 58.0, "Orange is exact. Blue is the linear tangent pair. The exact branch leaves with the same slope and then bends away.", size=13, fill="#9fb3c8", width_chars=34, line_height=18.0),
    ]

    full_box = (full_panel[0] + 68.0, full_panel[1] + 86.0, full_panel[2] - 28.0, full_panel[3] - 52.0)
    local_box = (local_panel[0] + 56.0, local_panel[1] + 100.0, local_panel[2] - 34.0, local_panel[3] - 170.0)

    parts.extend(
        draw_axes(
            box=full_box,
            x_ticks=((-math.pi, "-π"), (-math.pi / 2.0, "-π/2"), (0.0, "0"), (math.pi / 2.0, "π/2"), (math.pi, "π")),
            y_ticks=((-2.0, "-2.0"), (-1.0, "-1.0"), (0.0, "0"), (1.0, "1.0"), (2.0, "2.0")),
            x_range=system.x_range,
            y_range=system.y_range,
            x_label="angle θ",
            y_label="ω",
        )
    )

    for (theta, omega), (dtheta, domega) in field:
        x1, y1 = map_box(theta, omega, box=full_box, x_range=system.x_range, y_range=system.y_range)
        x2, y2 = map_box(theta + 0.18 * dtheta, omega + 0.18 * domega, box=full_box, x_range=system.x_range, y_range=system.y_range)
        parts.append(_line(x1, y1, x2, y2, stroke="#4b6580", width=1.3, opacity=0.9))

    for curve in curves:
        points = [map_box(theta, omega, box=full_box, x_range=system.x_range, y_range=system.y_range) for theta, omega in curve]
        if len(points) > 1:
            parts.append(_polyline(points, stroke="#4ade80", width=2.4, opacity=0.62))

    separatrix_upper = []
    separatrix_lower = []
    for index in range(420):
        theta = -math.pi + 2.0 * math.pi * index / 419.0
        omega = 2.0 * math.cos(0.5 * theta)
        separatrix_upper.append(map_box(theta, omega, box=full_box, x_range=system.x_range, y_range=system.y_range))
        separatrix_lower.append(map_box(theta, -omega, box=full_box, x_range=system.x_range, y_range=system.y_range))
    parts.append(_polyline(separatrix_upper, stroke="#f97316", width=3.2))
    parts.append(_polyline(separatrix_lower, stroke="#f97316", width=3.2))
    for theta, omega in system.fixed_points:
        x, y = map_box(theta, omega, box=full_box, x_range=system.x_range, y_range=system.y_range)
        parts.append(_circle(x, y, r=7.0, fill="#f8fafc"))
    legend_x = full_panel[2] - 250.0
    legend_y = full_panel[1] + 118.0
    parts.append(_line(legend_x, legend_y, legend_x + 28.0, legend_y, stroke="#f97316", width=4.0))
    parts.append(_text(legend_x + 38.0, legend_y + 5.0, "separatrix", size=13))
    parts.append(_line(legend_x, legend_y + 24.0, legend_x + 28.0, legend_y + 24.0, stroke="#4ade80", width=4.0))
    parts.append(_text(legend_x + 38.0, legend_y + 29.0, "sample trajectories", size=13))
    parts.append(_circle(legend_x + 14.0, legend_y + 49.0, r=5.0, fill="#f8fafc"))
    parts.append(_text(legend_x + 38.0, legend_y + 54.0, "fixed points", size=13))

    parts.extend(
        draw_axes(
            box=local_box,
            x_ticks=((-1.5, "-1.5"), (-0.75, "-0.75"), (0.0, "0"), (0.75, "0.75"), (1.5, "1.5")),
            y_ticks=((-1.5, "-1.5"), (-0.75, "-0.75"), (0.0, "0"), (0.75, "0.75"), (1.5, "1.5")),
            x_range=(-1.8, 1.8),
            y_range=(-1.8, 1.8),
            x_label="shift φ",
            y_label="ω",
        )
    )

    exact_top = []
    exact_bottom = []
    linear_up = []
    linear_down = []
    for index in range(320):
        phi = -1.8 + 3.6 * index / 319.0
        exact = 2.0 * math.sin(0.5 * phi)
        exact_top.append(map_box(phi, exact, box=local_box, x_range=(-1.8, 1.8), y_range=(-1.8, 1.8)))
        exact_bottom.append(map_box(phi, -exact, box=local_box, x_range=(-1.8, 1.8), y_range=(-1.8, 1.8)))
        linear_up.append(map_box(phi, phi, box=local_box, x_range=(-1.8, 1.8), y_range=(-1.8, 1.8)))
        linear_down.append(map_box(phi, -phi, box=local_box, x_range=(-1.8, 1.8), y_range=(-1.8, 1.8)))
    parts.append(_polyline(linear_up, stroke="#60a5fa", width=2.4, opacity=0.8))
    parts.append(_polyline(linear_down, stroke="#60a5fa", width=2.4, opacity=0.8))
    parts.append(_polyline(exact_top, stroke="#f97316", width=3.0))
    parts.append(_polyline(exact_bottom, stroke="#f97316", width=3.0))
    max_error = max(row.abs_error for row in rows)
    parts.append(_paragraph(local_panel[0] + 24.0, local_panel[3] - 104.0, "Exact barrier: H(θ, ω) = 1 - cos θ + ω² / 2 = 2.", size=14, fill="#f97316", width_chars=38, line_height=18.0, weight="700"))
    parts.append(_paragraph(local_panel[0] + 24.0, local_panel[3] - 72.0, f"For the sampled positive branch, the linear line overshoots the exact branch by {max_error:.3f} in ω by the time |φ| reaches π.", size=13, fill="#dce7f3", width_chars=42, line_height=18.0))
    parts.append(_paragraph(local_panel[0] + 24.0, local_panel[3] - 22.0, "The CSV sidecar and notebook keep the full error table; the figure only needs the geometry.", size=13, fill="#9fb3c8", width_chars=44, line_height=18.0))

    parts.append(_text(70.0, 868.0, "Generated from the standard-library pendulum pass: gallery system + exact separatrix formula + sampled error table.", size=14, fill="#9fb3c8"))
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n")


def render_pendulum_nonlinear_saddle_report(rows: Sequence[PendulumSeparatrixRow]) -> str:
    if not rows:
        raise ValueError("rows must not be empty")
    checkpoints = [rows[12], rows[32], rows[72], rows[-1]]
    lines = [
        "# Nonlinear saddle sidecar: the pendulum separatrix bends",
        "",
        "The linear saddle in the main gallery is still worth keeping. But it teaches only the first local sentence: one direction attracts and one direction repels.",
        "",
        "The simple pendulum adds the next sentence. The upright equilibrium is also a saddle, yet its invariant set is not a pair of straight lines across the whole plane. The barrier is an exact energy contour.",
        "",
        "## Exact object",
        "",
        "For the undamped pendulum",
        "",
        "- `θ' = ω`",
        "- `ω' = -sin θ`",
        "",
        "the conserved energy is",
        "",
        "- `H(θ, ω) = 1 - cos θ + ω² / 2`",
        "",
        "The upright equilibrium sits at `θ = π`, `ω = 0` with energy `H = 2`. So the separatrix is the exact level set `H = 2`.",
        "",
        "Shift the angle with `φ = θ - π`. On that local coordinate, the separatrix branches become",
        "",
        "- `ω = ± 2 sin(φ / 2)`",
        "",
        "and the linearized saddle only sees the tangent lines",
        "",
        "- `ω = ± φ`",
        "",
        "## What the sidecar measures",
        "",
        "The CSV sidecar tracks the positive branch for `0 ≤ φ ≤ π` and compares the exact `2 sin(φ/2)` branch to the linear `φ` tangent.",
        "",
        "Selected checkpoints:",
        "",
    ]
    for row in checkpoints:
        lines.append(f"- `φ = {row.shift:.3f}` → exact `ω = {row.exact_omega:.3f}`, linear `ω = {row.linear_omega:.3f}`, absolute error `= {row.abs_error:.3f}`")
    lines.extend(
        [
            "",
            "## Read of the picture",
            "",
            "- the full portrait shows closed oscillations below the barrier and the highlighted separatrix as the exact divide between trapped motion and rotation",
            "- the local zoom shows why the Jacobian is still useful: the exact branches leave the saddle with the same tangent lines the linear model predicts",
            "- the error panel shows why the local model should not be promoted into a global picture: the branch keeps bending while the linear line keeps climbing",
            "",
            "## Why this belongs in the repo",
            "",
            "The gallery already had a perfect straight saddle. This pass adds the missing counterweight: a system where the local saddle classification is right, but the global manifolds are curved enough that the local picture is visibly incomplete.",
            "",
            "## Caveat",
            "",
            "This sidecar uses the undamped pendulum because the energy integral is exact and readable. That makes it a geometry note, not a broad claim about every nonlinear saddle.",
            "",
            "Open `assets/pendulum-nonlinear-saddle.svg`, `assets/pendulum-nonlinear-saddle.png`, `assets/pendulum-nonlinear-saddle.csv`, and `notebooks/pendulum_nonlinear_saddle.ipynb` next.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_pendulum_nonlinear_saddle_report(rows: Sequence[PendulumSeparatrixRow], output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_pendulum_nonlinear_saddle_report(rows))
    return output


def write_pendulum_nonlinear_saddle_notebook(rows: Sequence[PendulumSeparatrixRow], output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Pendulum nonlinear saddle sidecar\n",
                    "\n",
                    "This notebook is the slower companion to `reports/pendulum-nonlinear-saddle.md`.\n",
                    "\n",
                    "The whole point is narrow: the upright pendulum is still a saddle, but its separatrix is an energy contour, not a pair of straight global eigenlines.\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Load the sampled branch table\n",
                    "\n",
                    "The CSV sidecar stores the positive branch `ω = 2 sin(φ/2)` beside the linear tangent `ω = φ`.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import csv\n",
                    "from pathlib import Path\n",
                    "\n",
                    "rows = []\n",
                    "with (Path('..') / 'assets' / 'pendulum-nonlinear-saddle.csv').open() as handle:\n",
                    "    for row in csv.DictReader(handle):\n",
                    "        rows.append({key: float(value) for key, value in row.items()})\n",
                    "rows[:3], rows[-3:]\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Re-state the exact object\n",
                    "\n",
                    "For the undamped pendulum, `H(θ, ω) = 1 - cos θ + ω²/2`. The upright equilibrium has `H = 2`, so the separatrix is the level set `H = 2`.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from phaseportraitlab.nonlinear_saddle import pendulum_energy\n",
                    "\n",
                    "samples = []\n",
                    "for row in rows[::40]:\n",
                    "    phi = row['shift']\n",
                    "    theta = 3.141592653589793 + phi\n",
                    "    omega = row['exact_omega']\n",
                    "    samples.append((round(phi, 4), round(pendulum_energy(theta, omega), 6)))\n",
                    "samples\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Read the approximation gap\n",
                    "\n",
                    "The local tangent is the right first derivative story, but the global branch keeps bending away from it.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "for row in rows[::45]:\n",
                    "    print(f\"phi={row['shift']:.3f} exact={row['exact_omega']:.3f} linear={row['linear_omega']:.3f} error={row['abs_error']:.3f}\")\n",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Problems worth keeping\n",
                    "\n",
                    "1. Compare one second nonlinear saddle only if it adds a genuinely new manifold geometry instead of repeating the same pendulum energy story.\n",
                    "2. Keep the local/global contrast explicit: the Jacobian is right locally, but the exact barrier is what closes the global picture.\n",
                    "3. If damping gets added later, separate the loss of energy conservation from the saddle geometry instead of mixing them into one note.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    import json
    output.write_text(json.dumps(notebook, indent=2) + "\n")
    return output


def write_pendulum_nonlinear_saddle_csv(rows: Sequence[PendulumSeparatrixRow], output: str | Path) -> Path:
    import csv

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["shift", "shift_deg", "exact_omega", "linear_omega", "abs_error"])
        for row in rows:
            writer.writerow([
                f"{row.shift:.8f}",
                f"{math.degrees(row.shift):.8f}",
                f"{row.exact_omega:.8f}",
                f"{row.linear_omega:.8f}",
                f"{row.abs_error:.8f}",
            ])
    return output


def crop_png_to_aspect(png_path: str | Path, *, aspect_width: int, aspect_height: int) -> bool:
    png_path = Path(png_path)
    sips = shutil.which("sips")
    if sips is None or not png_path.exists():
        return False
    probe = subprocess.run(
        [sips, "-g", "pixelWidth", "-g", "pixelHeight", str(png_path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    width = next(int(line.split(":", 1)[1].strip()) for line in probe if "pixelWidth:" in line)
    height = next(int(line.split(":", 1)[1].strip()) for line in probe if "pixelHeight:" in line)
    target_height = round(width * aspect_height / aspect_width)
    if target_height >= height:
        return True
    subprocess.run(
        [sips, "--cropToHeightWidth", str(target_height), str(width), str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def write_pendulum_nonlinear_saddle_packet(*, repo: str | Path) -> list[Path]:
    repo = Path(repo)
    assets = repo / "assets"
    reports = repo / "reports"
    notebooks = repo / "notebooks"
    rows = build_pendulum_separatrix_rows()

    svg_path = assets / "pendulum-nonlinear-saddle.svg"
    png_path = assets / "pendulum-nonlinear-saddle.png"
    csv_path = assets / "pendulum-nonlinear-saddle.csv"
    report_path = reports / "pendulum-nonlinear-saddle.md"
    notebook_path = notebooks / "pendulum_nonlinear_saddle.ipynb"

    render_pendulum_nonlinear_saddle_svg(rows, output=svg_path)
    export_png_from_svg(svg_path, png_path)
    crop_png_to_aspect(png_path, aspect_width=1560, aspect_height=900)
    write_pendulum_nonlinear_saddle_csv(rows, csv_path)
    write_pendulum_nonlinear_saddle_report(rows, report_path)
    write_pendulum_nonlinear_saddle_notebook(rows, notebook_path)
    return [svg_path, png_path, csv_path, report_path, notebook_path]
