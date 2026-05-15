from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Sequence

from .analysis import analyze_fixed_points
from .brusselator_atlas import (
    _append_gradient_legend,
    _blend_color,
    _escape,
    _nearest_cell,
    _peak_indices,
    _quantile,
    _three_color_gradient,
    atlas_axis_values,
)
from .integrate import rk4_step
from .systems import State, selkov


@dataclass(frozen=True)
class SelkovCycleMetrics:
    x_amplitude: float
    y_amplitude: float
    mean_radius: float
    period: float | None
    peak_count: int


@dataclass(frozen=True)
class SelkovAtlasCell:
    a: float
    b: float
    lower_threshold: float | None
    upper_threshold: float | None
    fixed_point: State
    trace: float
    determinant: float
    classification: str
    x_amplitude: float
    y_amplitude: float
    mean_radius: float
    period: float | None
    peak_count: int

    @property
    def in_oscillatory_band(self) -> bool:
        return (
            self.lower_threshold is not None
            and self.upper_threshold is not None
            and self.lower_threshold < self.b < self.upper_threshold
        )


def selkov_hopf_band(a: float) -> tuple[float, float] | None:
    if a <= 0.0:
        raise ValueError("a must be positive")
    discriminant = 1.0 - 8.0 * a
    if discriminant < 0.0:
        return None
    root = math.sqrt(max(0.0, discriminant))
    lower_sq = (1.0 - 2.0 * a - root) / 2.0
    upper_sq = (1.0 - 2.0 * a + root) / 2.0
    if upper_sq <= 0.0:
        return None
    lower = math.sqrt(max(0.0, lower_sq))
    upper = math.sqrt(max(0.0, upper_sq))
    return (lower, upper)


def estimate_selkov_cycle_metrics(
    a: float,
    b: float,
    *,
    dt: float = 0.02,
    settle_time: float = 150.0,
    sample_time: float = 90.0,
) -> SelkovCycleMetrics:
    band = selkov_hopf_band(a)
    if band is None or not (band[0] < b < band[1]):
        return SelkovCycleMetrics(0.0, 0.0, 0.0, None, 0)

    if dt <= 0.0:
        raise ValueError("dt must be positive")
    if settle_time <= 0.0 or sample_time <= 0.0:
        raise ValueError("settle_time and sample_time must be positive")

    fixed_point = (b, b / (a + b * b))
    derivatives = selkov(a=a, b=b).derivatives
    total_steps = int((settle_time + sample_time) / dt)
    burn = int(settle_time / dt)
    state = (max(0.04, 0.62 * b), fixed_point[1] + 0.26)

    tail: list[State] = []
    for step_index in range(total_steps):
        state = rk4_step(derivatives, state, dt)
        if step_index >= burn:
            tail.append(state)

    if not tail:
        return SelkovCycleMetrics(0.0, 0.0, 0.0, None, 0)

    xs = [point[0] for point in tail]
    ys = [point[1] for point in tail]
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    x_amplitude = x_span / 2.0
    y_amplitude = y_span / 2.0
    radii = [math.hypot(x - fixed_point[0], y - fixed_point[1]) for x, y in tail]
    mean_radius = sum(radii) / len(radii)

    period: float | None = None
    peaks = _peak_indices(xs)
    if len(peaks) >= 3 and x_amplitude > 1e-4:
        spacings = [(peaks[index + 1] - peaks[index]) * dt for index in range(len(peaks) - 1)]
        period = sum(spacings) / len(spacings)

    return SelkovCycleMetrics(x_amplitude, y_amplitude, mean_radius, period, len(peaks))


def build_selkov_parameter_atlas(
    a_values: Sequence[float],
    b_values: Sequence[float],
) -> list[SelkovAtlasCell]:
    if not a_values or not b_values:
        raise ValueError("a_values and b_values must not be empty")

    cells: list[SelkovAtlasCell] = []
    for b in b_values:
        for a in a_values:
            band = selkov_hopf_band(float(a))
            item = analyze_fixed_points(selkov(a=float(a), b=float(b)))[0]
            metrics = estimate_selkov_cycle_metrics(float(a), float(b)) if band and band[0] < b < band[1] else SelkovCycleMetrics(0.0, 0.0, 0.0, None, 0)
            cells.append(
                SelkovAtlasCell(
                    a=float(a),
                    b=float(b),
                    lower_threshold=None if band is None else band[0],
                    upper_threshold=None if band is None else band[1],
                    fixed_point=item.point,
                    trace=item.trace,
                    determinant=item.determinant,
                    classification=item.classification,
                    x_amplitude=metrics.x_amplitude,
                    y_amplitude=metrics.y_amplitude,
                    mean_radius=metrics.mean_radius,
                    period=metrics.period,
                    peak_count=metrics.peak_count,
                )
            )
    return cells


def default_selkov_parameter_atlas() -> list[SelkovAtlasCell]:
    return build_selkov_parameter_atlas(
        atlas_axis_values(0.02, 0.12, 11),
        atlas_axis_values(0.15, 1.05, 19),
    )


def render_selkov_parameter_atlas(
    cells: Sequence[SelkovAtlasCell],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not cells:
        raise ValueError("cells must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    a_values = sorted({cell.a for cell in cells})
    b_values = sorted({cell.b for cell in cells})
    a_min, a_max = a_values[0], a_values[-1]
    b_min, b_max = b_values[0], b_values[-1]
    unstable_cells = [cell for cell in cells if cell.in_oscillatory_band and cell.period is not None]
    amp_values = [cell.x_amplitude for cell in unstable_cells]
    period_values = [cell.period or 0.0 for cell in unstable_cells]
    max_amp = max(amp_values, default=0.0)
    max_period = max(period_values, default=0.0)
    amp_cap = _quantile(amp_values, 0.95) if amp_values else 0.0
    period_cap = _quantile(period_values, 0.95) if period_values else 0.0

    width = 1580
    height = 1620
    left = 106.0
    right = 360.0
    panel_width = width - left - right
    top = 126.0
    panel_height = 356.0
    gap = 58.0

    panel_y_positions = [top + index * (panel_height + gap) for index in range(3)]
    x_step = panel_width / len(a_values)
    y_step = panel_height / len(b_values)

    def x_for(a: float) -> float:
        return left + (a - a_min) / (a_max - a_min) * panel_width

    def y_for(b: float, panel_top: float) -> float:
        return panel_top + panel_height - (b - b_min) / (b_max - b_min) * panel_height

    def cell_rect(cell: SelkovAtlasCell, panel_top: float) -> tuple[float, float, float, float]:
        ix = a_values.index(cell.a)
        iy = b_values.index(cell.b)
        x = left + ix * x_step
        y = panel_top + panel_height - (iy + 1) * y_step
        return (x, y, x_step, y_step)

    def phase_color(cell: SelkovAtlasCell) -> str:
        if not cell.in_oscillatory_band:
            if cell.lower_threshold is None or cell.upper_threshold is None:
                return "#16324f"
            distance = min(abs(cell.b - cell.lower_threshold), abs(cell.b - cell.upper_threshold))
            scale = max(0.0, min(1.0, distance / 0.18))
            return _blend_color("#0b2037", "#2563eb", scale)
        assert cell.lower_threshold is not None and cell.upper_threshold is not None
        center = (cell.lower_threshold + cell.upper_threshold) / 2.0
        half_width = max(1e-9, (cell.upper_threshold - cell.lower_threshold) / 2.0)
        depth = 1.0 - min(1.0, abs(cell.b - center) / half_width)
        return _blend_color("#3b1220", "#fb7185", depth)

    def amplitude_color(cell: SelkovAtlasCell) -> str:
        if cell.x_amplitude <= 0.0 or amp_cap <= 1e-12:
            return "#0b1722"
        scale = math.sqrt(min(1.0, cell.x_amplitude / amp_cap))
        return _three_color_gradient(scale, "#0b1722", "#0f766e", "#fde68a")

    def period_color(cell: SelkovAtlasCell) -> str:
        if cell.period is None or period_cap <= 1e-12:
            return "#0b1722"
        scale = math.sqrt(min(1.0, cell.period / period_cap))
        return _three_color_gradient(scale, "#0b1722", "#7c3aed", "#bef264")

    def hopf_segments(panel_top: float, branch: int) -> list[str]:
        segments: list[list[tuple[float, float]]] = []
        current: list[tuple[float, float]] = []
        for index in range(220):
            a = a_min + (a_max - a_min) * index / 219.0
            band = selkov_hopf_band(a)
            if band is None:
                if len(current) > 1:
                    segments.append(current)
                current = []
                continue
            b = band[branch]
            if not (b_min <= b <= b_max):
                if len(current) > 1:
                    segments.append(current)
                current = []
                continue
            current.append((x_for(a), y_for(b, panel_top)))
        if len(current) > 1:
            segments.append(current)
        return [
            '<polyline fill="none" stroke="#fbbf24" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" points="' + ' '.join(f"{x:.2f},{y:.2f}" for x, y in segment) + '"/>'
            for segment in segments
        ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left:.0f}" y="56" fill="#e6edf3" font-size="34" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Selkov parameter atlas")}</text>',
        f'<text x="{left:.0f}" y="86" fill="#9fb3c8" font-size="18" font-family="Helvetica, Arial, sans-serif">Exact local theory gives two Hopf curves when a &lt; 1/8, so the oscillatory regime is a finite band in parameter space rather than a one-sided half-plane.</text>',
    ]

    panel_titles = [
        "local side of the two exact Hopf curves",
        "long-time x-amplitude inside the oscillatory band",
        "estimated cycle period inside the oscillatory band",
    ]
    subtitle_lines = [
        "Blue cells are locally attracting. Red cells sit between the two gold Hopf boundaries, where the fixed point repels and the glycolytic oscillation appears.",
        "Outside the band the amplitude is pinned to zero because the fixed point attracts there. Inside the band the value comes from RK4 tail measurements.",
        "Periods come from repeated x-peaks after transients decay. The band narrows as a approaches 1/8.",
    ]
    color_functions = [phase_color, amplitude_color, period_color]

    for panel_index, panel_top in enumerate(panel_y_positions):
        lines.append(f'<rect x="{left:.2f}" y="{panel_top:.2f}" width="{panel_width:.2f}" height="{panel_height:.2f}" rx="20" fill="#122131" stroke="#5e7fa3" stroke-width="2"/>')
        lines.append(f'<text x="{left + 18:.2f}" y="{panel_top + 30:.2f}" fill="#dce7f3" font-size="20" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(panel_titles[panel_index])}</text>')
        lines.append(f'<text x="{left + 18:.2f}" y="{panel_top + 54:.2f}" fill="#9fb3c8" font-size="14" font-family="Helvetica, Arial, sans-serif">{_escape(subtitle_lines[panel_index])}</text>')

        for cell in cells:
            x, y, w, h = cell_rect(cell, panel_top)
            lines.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{w + 0.4:.2f}" height="{h + 0.4:.2f}" fill="{color_functions[panel_index](cell)}" opacity="0.98"/>'
            )

        lines.extend(hopf_segments(panel_top, 0))
        lines.extend(hopf_segments(panel_top, 1))

        for tick in range(6):
            a_tick = a_min + (a_max - a_min) * tick / 5.0
            x = x_for(a_tick)
            lines.append(f'<line x1="{x:.2f}" y1="{panel_top + 66:.2f}" x2="{x:.2f}" y2="{panel_top + panel_height:.2f}" stroke="#223445" stroke-width="1" opacity="0.8"/>')
            lines.append(f'<text x="{x:.2f}" y="{panel_top + panel_height + 24:.2f}" fill="#8aa3bc" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{a_tick:.3f}</text>')
        for tick in range(6):
            b_tick = b_min + (b_max - b_min) * tick / 5.0
            y = y_for(b_tick, panel_top)
            lines.append(f'<line x1="{left:.2f}" y1="{y:.2f}" x2="{left + panel_width:.2f}" y2="{y:.2f}" stroke="#223445" stroke-width="1" opacity="0.8"/>')
            lines.append(f'<text x="{left - 14:.2f}" y="{y + 4:.2f}" fill="#8aa3bc" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{b_tick:.2f}</text>')

        lines.append(f'<text x="{left + panel_width / 2:.2f}" y="{panel_top + panel_height + 48:.2f}" fill="#dce7f3" font-size="16" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">a</text>')
        lines.append(f'<text x="{left - 68:.2f}" y="{panel_top + panel_height / 2:.2f}" fill="#dce7f3" font-size="16" text-anchor="middle" transform="rotate(-90 {left - 68:.2f} {panel_top + panel_height / 2:.2f})" font-family="Helvetica, Arial, sans-serif">b</text>')

    legend_x = left + panel_width + 28.0
    legend_width = 34.0
    legend_height = 210.0
    label_x = legend_x + legend_width + 14.0

    _append_gradient_legend(
        lines,
        x=legend_x,
        y=panel_y_positions[0] + 94.0,
        width=legend_width,
        height=legend_height,
        stops=[(0.0, "#2563eb"), (1.0, "#fb7185")],
        tick_labels=[("stable", 0.0), ("Hopf edge", 0.5), ("inside band", 1.0)],
        label_x=label_x,
        caption="local side",
    )
    _append_gradient_legend(
        lines,
        x=legend_x,
        y=panel_y_positions[1] + 118.0,
        width=legend_width,
        height=legend_height,
        stops=[(0.0, "#0b1722"), (0.5, "#0f766e"), (1.0, "#fde68a")],
        tick_labels=[("0.00", 0.0), (f"{amp_cap / 2:.2f}", 0.5), (f"{amp_cap:.2f}", 1.0)],
        label_x=label_x,
        caption="x amplitude (95% cap)",
    )
    _append_gradient_legend(
        lines,
        x=legend_x,
        y=panel_y_positions[2] + 118.0,
        width=legend_width,
        height=legend_height,
        stops=[(0.0, "#0b1722"), (0.5, "#7c3aed"), (1.0, "#bef264")],
        tick_labels=[("0.0", 0.0), (f"{period_cap / 2:.1f}", 0.5), (f"{period_cap:.1f}", 1.0)],
        label_x=label_x,
        caption="period (95% cap)",
    )

    samples = [
        _nearest_cell(cells, 0.05, 0.20),
        _nearest_cell(cells, 0.05, 0.45),
        _nearest_cell(cells, 0.08, 0.60),
        _nearest_cell(cells, 0.08, 0.95),
    ]
    callout_x = legend_x - 16.0
    callout_y = height - 332.0
    callout_w = width - callout_x - 34.0
    lines.append(f'<rect x="{callout_x:.2f}" y="{callout_y:.2f}" width="{callout_w:.2f}" height="196" rx="18" fill="#0b1722" stroke="#5e7fa3" stroke-width="1.6"/>')
    lines.append(f'<text x="{callout_x + 18:.2f}" y="{callout_y + 28:.2f}" fill="#dce7f3" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">Anchor readings</text>')
    for index, cell in enumerate(samples):
        status = "fixed point attracts" if not cell.in_oscillatory_band else "limit cycle measured"
        period_text = "—" if cell.period is None else f"{cell.period:.2f}"
        y = callout_y + 56.0 + index * 34.0
        lines.append(f'<text x="{callout_x + 18:.2f}" y="{y:.2f}" fill="#dce7f3" font-size="13" font-family="Helvetica, Arial, sans-serif">a={cell.a:.3f}, b={cell.b:.2f} → {status}</text>')
        lines.append(f'<text x="{callout_x + 30:.2f}" y="{y + 17:.2f}" fill="#9fb3c8" font-size="12" font-family="Helvetica, Arial, sans-serif">local={cell.classification}, x amp={cell.x_amplitude:.2f}, period={period_text}</text>')

    lines.append(f'<text x="{left:.0f}" y="{height - 44:.0f}" fill="#9fb3c8" font-size="13" font-family="Helvetica, Arial, sans-serif">Measurement recipe: RK4 with dt = 0.02 for 240 time units, using the last 90 time units to estimate amplitude and period inside the oscillatory band.</text>')
    lines.append(f'<text x="{left:.0f}" y="{height - 22:.0f}" fill="#9fb3c8" font-size="13" font-family="Helvetica, Arial, sans-serif">Color bars are capped at the 95th percentile for readability; the full scan reaches x amplitude {max_amp:.2f} and period {max_period:.2f} at the widest part of the band.</text>')
    lines.append('</svg>')

    output.write_text("\n".join(lines) + "\n")



def render_selkov_parameter_report(cells: Sequence[SelkovAtlasCell]) -> str:
    if not cells:
        raise ValueError("cells must not be empty")

    unstable_cells = [cell for cell in cells if cell.in_oscillatory_band and cell.period is not None]
    max_amp = max((cell.x_amplitude for cell in unstable_cells), default=0.0)
    max_period = max((cell.period or 0.0 for cell in unstable_cells), default=0.0)
    amp_cap = _quantile([cell.x_amplitude for cell in unstable_cells], 0.95) if unstable_cells else 0.0
    period_cap = _quantile([cell.period or 0.0 for cell in unstable_cells], 0.95) if unstable_cells else 0.0

    anchors = [
        _nearest_cell(cells, 0.05, 0.20),
        _nearest_cell(cells, 0.05, 0.45),
        _nearest_cell(cells, 0.08, 0.60),
        _nearest_cell(cells, 0.08, 0.95),
    ]

    band_005 = selkov_hopf_band(0.05)
    band_008 = selkov_hopf_band(0.08)
    band_010 = selkov_hopf_band(0.10)

    lines = [
        "# Selkov parameter atlas",
        "",
        "This report adds a second chemistry-facing oscillator to the repo: the Selkov glycolysis model.",
        "",
        "For the Selkov system",
        "",
        "```text",
        "dx/dt = -x + a y + x^2 y",
        "dy/dt = b - a y - x^2 y",
        "```",
        "",
        "the positive fixed point is `(x*, y*) = (b, b / (a + b^2))` and the Jacobian determinant is exactly `a + b^2`, so the local question is controlled by the trace.",
        "Writing `s = a + b^2`, the trace-zero condition becomes `s^2 - s + 2a = 0`, which yields two exact Hopf boundaries when `a < 1/8`.",
        "That makes the local oscillatory regime a **finite band** in `b` instead of the Brusselator's one-sided region above a single curve.",
        "",
        "## Exact local window",
        "",
        f"- at `a = 0.05`, the exact local oscillatory band is `b ∈ ({band_005[0]:.3f}, {band_005[1]:.3f})`",
        f"- at `a = 0.08`, the exact local oscillatory band is `b ∈ ({band_008[0]:.3f}, {band_008[1]:.3f})`",
        f"- at `a = 0.10`, the exact local oscillatory band is `b ∈ ({band_010[0]:.3f}, {band_010[1]:.3f})`",
        "- as `a` approaches `1/8`, the two Hopf curves pinch together and the oscillatory band collapses",
        "",
        "The generated SVG `assets/selkov-parameter-atlas.svg` keeps the exact local band separate from the numerical long-time cycle measurements.",
        "",
        "## What the scan says",
        "",
        f"- most sampled oscillatory cells stay below about `{amp_cap:.2f}` in `x` amplitude, with a widest-band extreme near `{max_amp:.2f}`",
        f"- most measured periods stay below about `{period_cap:.2f}`, with an extreme value near `{max_period:.2f}`",
        "- unlike the Brusselator atlas, the Selkov amplitude map fades back to zero on the high-`b` side because the fixed point becomes locally attracting again after the upper Hopf boundary",
        "- the widest and strongest oscillations sit near small `a`, where the exact band is broadest",
        "",
        "## Anchor settings",
        "",
        "| a | b | local type | x amplitude | y amplitude | period | reading |",
        "| ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for cell in anchors:
        reading = "stable fixed point" if not cell.in_oscillatory_band else "self-sustained cycle"
        period_text = "—" if cell.period is None else f"{cell.period:.2f}"
        lines.append(
            f"| {cell.a:.3f} | {cell.b:.2f} | {cell.classification} | {cell.x_amplitude:.2f} | {cell.y_amplitude:.2f} | {period_text} | {reading} |"
        )

    lines.extend(
        [
            "",
            "## Measurement recipe and caveat",
            "",
            "The numerical panels use RK4 with `dt = 0.02`, integrate for `240` time units, and measure the final `90` time units.",
            "That is enough to make the stable → oscillatory → stable transition visible on this grid, but it is still a **finite-time** estimate of the cycle size and period.",
            "The point of the atlas is to connect exact Jacobian theory to a visible long-time glycolytic oscillation, not to claim the finite grid is the whole bifurcation theory.",
        ]
    )
    return "\n".join(lines) + "\n"



def write_selkov_parameter_report(cells: Sequence[SelkovAtlasCell], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_selkov_parameter_report(cells))
