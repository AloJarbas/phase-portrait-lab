from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Sequence

from .analysis import analyze_fixed_points
from .integrate import rk4_step
from .systems import State, brusselator
from .brusselator_sweep import brusselator_hopf_threshold


@dataclass(frozen=True)
class BrusselatorCycleMetrics:
    x_amplitude: float
    y_amplitude: float
    mean_radius: float
    period: float | None
    peak_count: int


@dataclass(frozen=True)
class BrusselatorAtlasCell:
    a: float
    b: float
    threshold: float
    hopf_offset: float
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
    def oscillatory_side(self) -> bool:
        return self.hopf_offset > 0.0


def atlas_axis_values(start: float, stop: float, steps: int) -> list[float]:
    if steps < 2:
        raise ValueError("steps must be at least 2")
    if stop < start:
        raise ValueError("stop must be at least start")
    step = (stop - start) / (steps - 1)
    return [start + index * step for index in range(steps)]


def estimate_brusselator_cycle_metrics(
    a: float,
    b: float,
    *,
    dt: float = 0.015,
    settle_time: float = 105.0,
    sample_time: float = 75.0,
) -> BrusselatorCycleMetrics:
    threshold = brusselator_hopf_threshold(a)
    if b <= threshold:
        return BrusselatorCycleMetrics(0.0, 0.0, 0.0, None, 0)

    if dt <= 0.0:
        raise ValueError("dt must be positive")
    if settle_time <= 0.0 or sample_time <= 0.0:
        raise ValueError("settle_time and sample_time must be positive")

    fixed_point = (a, b / a)
    derivatives = brusselator(a=a, b=b).derivatives
    total_steps = int((settle_time + sample_time) / dt)
    burn = int(settle_time / dt)
    state = (a + max(0.22, 0.18 * a), fixed_point[1] + 0.22)

    tail: list[State] = []
    for step_index in range(total_steps):
        state = rk4_step(derivatives, state, dt)
        if step_index >= burn:
            tail.append(state)

    if not tail:
        return BrusselatorCycleMetrics(0.0, 0.0, 0.0, None, 0)

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

    return BrusselatorCycleMetrics(x_amplitude, y_amplitude, mean_radius, period, len(peaks))


def build_brusselator_parameter_atlas(
    a_values: Sequence[float],
    b_values: Sequence[float],
) -> list[BrusselatorAtlasCell]:
    if not a_values or not b_values:
        raise ValueError("a_values and b_values must not be empty")

    cells: list[BrusselatorAtlasCell] = []
    for b in b_values:
        for a in a_values:
            threshold = brusselator_hopf_threshold(float(a))
            item = analyze_fixed_points(brusselator(a=float(a), b=float(b)))[0]
            metrics = estimate_brusselator_cycle_metrics(float(a), float(b)) if b > threshold else BrusselatorCycleMetrics(0.0, 0.0, 0.0, None, 0)
            cells.append(
                BrusselatorAtlasCell(
                    a=float(a),
                    b=float(b),
                    threshold=threshold,
                    hopf_offset=float(b) - threshold,
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


def default_brusselator_parameter_atlas() -> list[BrusselatorAtlasCell]:
    return build_brusselator_parameter_atlas(
        atlas_axis_values(0.6, 2.0, 13),
        atlas_axis_values(1.0, 6.0, 19),
    )


def render_brusselator_parameter_atlas(
    cells: Sequence[BrusselatorAtlasCell],
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
    unstable_cells = [cell for cell in cells if cell.period is not None]
    amp_values = [cell.x_amplitude for cell in unstable_cells]
    period_values = [cell.period or 0.0 for cell in unstable_cells]
    max_amp = max(amp_values, default=0.0)
    max_period = max(period_values, default=0.0)
    amp_cap = _quantile(amp_values, 0.95) if amp_values else 0.0
    period_cap = _quantile(period_values, 0.95) if period_values else 0.0

    width = 1420
    height = 1620
    left = 106.0
    right = 216.0
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

    def cell_rect(cell: BrusselatorAtlasCell, panel_top: float) -> tuple[float, float, float, float]:
        ix = a_values.index(cell.a)
        iy = b_values.index(cell.b)
        x = left + ix * x_step
        y = panel_top + panel_height - (iy + 1) * y_step
        return (x, y, x_step, y_step)

    def phase_color(cell: BrusselatorAtlasCell) -> str:
        if cell.hopf_offset <= 0.0:
            scale = max(0.0, min(1.0, abs(cell.hopf_offset) / 2.4))
            return _blend_color("#0b2037", "#2563eb", scale)
        scale = max(0.0, min(1.0, cell.hopf_offset / 1.25))
        return _blend_color("#3b1220", "#fb7185", scale)

    def amplitude_color(cell: BrusselatorAtlasCell) -> str:
        if cell.x_amplitude <= 0.0 or amp_cap <= 1e-12:
            return "#0b1722"
        scale = math.sqrt(min(1.0, cell.x_amplitude / amp_cap))
        return _three_color_gradient(scale, "#0b1722", "#0f766e", "#fde68a")

    def period_color(cell: BrusselatorAtlasCell) -> str:
        if cell.period is None or period_cap <= 1e-12:
            return "#0b1722"
        scale = math.sqrt(min(1.0, cell.period / period_cap))
        return _three_color_gradient(scale, "#0b1722", "#7c3aed", "#bef264")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left:.0f}" y="56" fill="#e6edf3" font-size="34" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Brusselator parameter atlas")}</text>',
        f'<text x="{left:.0f}" y="86" fill="#9fb3c8" font-size="18" font-family="Helvetica, Arial, sans-serif">Exact Hopf curve: B = 1 + A². The first panel is local theory; the lower two panels add long-time cycle size and timing on the oscillatory side.</text>',
    ]

    panel_titles = [
        "local side of the Hopf curve (exact from the Jacobian trace)",
        "long-time x-amplitude of the self-sustained cycle",
        "estimated cycle period after transients decay",
    ]
    subtitle_lines = [
        "Blue cells spiral back to the fixed point; red cells sit on the oscillatory side. The gold curve is the exact Hopf threshold.",
        "Below threshold the amplitude is set to zero because the fixed point attracts. Above threshold the value comes from RK4 tail measurements.",
        "Periods are measured from repeated x-peaks in the tail window. Slow cycles appear brighter in this panel.",
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

        curve_points = []
        for index in range(180):
            a = a_min + (a_max - a_min) * index / 179.0
            b = brusselator_hopf_threshold(a)
            curve_points.append((x_for(a), y_for(max(b_min, min(b_max, b)), panel_top)))
        curve_coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in curve_points)
        lines.append(f'<polyline fill="none" stroke="#fbbf24" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" points="{curve_coords}"/>')

        for tick in range(6):
            a_tick = a_min + (a_max - a_min) * tick / 5.0
            x = x_for(a_tick)
            lines.append(f'<line x1="{x:.2f}" y1="{panel_top + 66:.2f}" x2="{x:.2f}" y2="{panel_top + panel_height:.2f}" stroke="#223445" stroke-width="1" opacity="0.8"/>')
            lines.append(f'<text x="{x:.2f}" y="{panel_top + panel_height + 24:.2f}" fill="#8aa3bc" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{a_tick:.2f}</text>')
        for tick in range(6):
            b_tick = b_min + (b_max - b_min) * tick / 5.0
            y = y_for(b_tick, panel_top)
            lines.append(f'<line x1="{left:.2f}" y1="{y:.2f}" x2="{left + panel_width:.2f}" y2="{y:.2f}" stroke="#223445" stroke-width="1" opacity="0.8"/>')
            lines.append(f'<text x="{left - 14:.2f}" y="{y + 4:.2f}" fill="#8aa3bc" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{b_tick:.2f}</text>')

        lines.append(f'<text x="{left + panel_width / 2:.2f}" y="{panel_top + panel_height + 48:.2f}" fill="#dce7f3" font-size="16" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">A</text>')
        lines.append(f'<text x="{left - 68:.2f}" y="{panel_top + panel_height / 2:.2f}" fill="#dce7f3" font-size="16" text-anchor="middle" transform="rotate(-90 {left - 68:.2f} {panel_top + panel_height / 2:.2f})" font-family="Helvetica, Arial, sans-serif">B</text>')

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
        tick_labels=[("stable", 0.0), ("threshold", 0.5), ("oscillatory", 1.0)],
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
        tick_labels=[(f"0.00", 0.0), (f"{amp_cap / 2:.2f}", 0.5), (f"{amp_cap:.2f}", 1.0)],
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
        tick_labels=[(f"0.0", 0.0), (f"{period_cap / 2:.1f}", 0.5), (f"{period_cap:.1f}", 1.0)],
        label_x=label_x,
        caption="period (95% cap)",
    )

    samples = [
        _nearest_cell(cells, 0.8, brusselator_hopf_threshold(0.8) - 0.25),
        _nearest_cell(cells, 1.0, brusselator_hopf_threshold(1.0) + 0.35),
        _nearest_cell(cells, 1.5, brusselator_hopf_threshold(1.5) + 0.35),
        _nearest_cell(cells, 2.0, brusselator_hopf_threshold(2.0) + 0.35),
    ]
    callout_x = legend_x - 16.0
    callout_y = height - 292.0
    callout_w = right + 118.0
    lines.append(f'<rect x="{callout_x:.2f}" y="{callout_y:.2f}" width="{callout_w:.2f}" height="204" rx="18" fill="#0b1722" stroke="#5e7fa3" stroke-width="1.6"/>')
    lines.append(f'<text x="{callout_x + 18:.2f}" y="{callout_y + 28:.2f}" fill="#dce7f3" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">Anchor readings</text>')
    for index, cell in enumerate(samples):
        status = "fixed point attracts" if cell.hopf_offset <= 0.0 else "limit cycle measured"
        period_text = "—" if cell.period is None else f"{cell.period:.2f}"
        y = callout_y + 56.0 + index * 34.0
        lines.append(f'<text x="{callout_x + 18:.2f}" y="{y:.2f}" fill="#dce7f3" font-size="13" font-family="Helvetica, Arial, sans-serif">A={cell.a:.2f}, B={cell.b:.2f}, Δ={cell.hopf_offset:+.2f} → {status}</text>')
        lines.append(f'<text x="{callout_x + 30:.2f}" y="{y + 17:.2f}" fill="#9fb3c8" font-size="12" font-family="Helvetica, Arial, sans-serif">x amp={cell.x_amplitude:.2f}, y amp={cell.y_amplitude:.2f}, period={period_text}</text>')

    lines.append(f'<text x="{left:.0f}" y="{height - 44:.0f}" fill="#9fb3c8" font-size="13" font-family="Helvetica, Arial, sans-serif">Measurement recipe: RK4 with dt = 0.015 for 180 time units, using the last 75 time units to estimate amplitude and period on the unstable side.</text>')
    lines.append(f'<text x="{left:.0f}" y="{height - 22:.0f}" fill="#9fb3c8" font-size="13" font-family="Helvetica, Arial, sans-serif">Color bars are capped at the 95th percentile for readability; the full scan reaches x amplitude {max_amp:.2f} and period {max_period:.2f} in the far low-A / high-B corner.</text>')
    lines.append('</svg>')

    output.write_text("\n".join(lines) + "\n")


def render_brusselator_parameter_report(cells: Sequence[BrusselatorAtlasCell]) -> str:
    if not cells:
        raise ValueError("cells must not be empty")

    unstable_cells = [cell for cell in cells if cell.oscillatory_side and cell.period is not None]
    max_amp = max(cell.x_amplitude for cell in unstable_cells)
    min_amp = min(cell.x_amplitude for cell in unstable_cells)
    max_period = max(cell.period or 0.0 for cell in unstable_cells)
    min_period = min(cell.period or 0.0 for cell in unstable_cells)
    amp_cap = _quantile([cell.x_amplitude for cell in unstable_cells], 0.95)
    period_cap = _quantile([cell.period or 0.0 for cell in unstable_cells], 0.95)

    anchors = [
        _nearest_cell(cells, 0.8, brusselator_hopf_threshold(0.8) - 0.25),
        _nearest_cell(cells, 0.8, brusselator_hopf_threshold(0.8) + 0.35),
        _nearest_cell(cells, 1.0, brusselator_hopf_threshold(1.0) + 0.35),
        _nearest_cell(cells, 1.5, brusselator_hopf_threshold(1.5) + 0.35),
        _nearest_cell(cells, 2.0, brusselator_hopf_threshold(2.0) + 0.35),
    ]

    lines = [
        "# Brusselator parameter atlas",
        "",
        "This report extends the one-parameter Hopf sweep into a two-parameter chemistry map.",
        "",
        "For the Brusselator",
        "",
        "```text",
        "dx/dt = A + x^2 y - (B + 1)x",
        "dy/dt = Bx - x^2 y",
        "```",
        "",
        "the fixed point stays at `(x*, y*) = (A, B / A)` and the Jacobian trace is exactly `B - 1 - A^2`.",
        "So the Hopf curve is `B = 1 + A^2`: below it the fixed point is a stable spiral; above it the fixed point repels and a self-sustained cycle appears.",
        "",
        "The generated SVG `assets/brusselator-parameter-atlas.svg` keeps those two readings separate:",
        "",
        "- the top panel is exact local theory from the Jacobian",
        "- the middle panel adds a numerical estimate of long-time `x` amplitude",
        "- the bottom panel adds a numerical period estimate from peak spacing",
        "",
        "## What the scan says",
        "",
        f"- most unstable sampled cells stay below about `{amp_cap:.2f}` in `x` amplitude, while the far low-`A` / high-`B` corner stretches out to `{max_amp:.2f}`",
        f"- most measured periods stay below about `{period_cap:.2f}`, with an extreme corner value near `{max_period:.2f}`",
        "- larger `A` values move the Hopf curve upward while also shortening the cycle period for comparable positive offsets above threshold",
        "- below threshold the report sets the oscillation amplitude to zero on purpose: the exact local theory says the fixed point attracts there, even if finite-time transients can decay slowly near the boundary",
        "",
        "## Anchor settings",
        "",
        "| A | B | Δ = B - (1 + A²) | local type | x amplitude | y amplitude | period | reading |",
        "| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for cell in anchors:
        reading = "stable fixed point" if cell.hopf_offset <= 0.0 else "self-sustained cycle"
        period_text = "—" if cell.period is None else f"{cell.period:.2f}"
        lines.append(
            f"| {cell.a:.2f} | {cell.b:.2f} | {cell.hopf_offset:+.2f} | {cell.classification} | {cell.x_amplitude:.2f} | {cell.y_amplitude:.2f} | {period_text} | {reading} |"
        )

    lines.extend(
        [
            "",
            "## Measurement recipe and caveat",
            "",
            "The numerical panels use RK4 with `dt = 0.015`, integrate for `180` time units, and measure the final `75` time units.",
            "That is enough to make the post-Hopf growth clear on this grid, but it is still a **finite-time** estimate rather than a proof of the global bifurcation structure.",
            "The point of the atlas is to bridge exact local stability and the visible long-time chemical oscillation, not to pretend the finite grid is the full theory.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_brusselator_parameter_report(cells: Sequence[BrusselatorAtlasCell], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_brusselator_parameter_report(cells))


def _peak_indices(values: Sequence[float]) -> list[int]:
    if len(values) < 3:
        return []
    center = sum(values) / len(values)
    span = max(values) - min(values)
    threshold = center + 0.15 * span
    peaks: list[int] = []
    for index in range(1, len(values) - 1):
        if values[index] > values[index - 1] and values[index] >= values[index + 1] and values[index] >= threshold:
            if peaks and index - peaks[-1] < 8:
                if values[index] > values[peaks[-1]]:
                    peaks[-1] = index
                continue
            peaks.append(index)
    return peaks


def _append_gradient_legend(
    lines: list[str],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    stops: Sequence[tuple[float, str]],
    tick_labels: Sequence[tuple[str, float]],
    label_x: float,
    caption: str,
) -> None:
    gradient_id = f"legend-{abs(hash((x, y, caption))) % 10_000_000}"
    lines.append(f'<linearGradient id="{gradient_id}" x1="0" y1="1" x2="0" y2="0">')
    for offset, color in stops:
        lines.append(f'  <stop offset="{offset * 100:.1f}%" stop-color="{color}"/>')
    lines.append('</linearGradient>')
    lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" rx="12" fill="url(#{gradient_id})" stroke="#5e7fa3" stroke-width="1.5"/>')
    lines.append(f'<text x="{x:.2f}" y="{y - 14:.2f}" fill="#dce7f3" font-size="14" font-family="Helvetica, Arial, sans-serif">{_escape(caption)}</text>')
    for label, fraction in tick_labels:
        tick_y = y + height - fraction * height
        lines.append(f'<line x1="{x + width + 4:.2f}" y1="{tick_y:.2f}" x2="{x + width + 10:.2f}" y2="{tick_y:.2f}" stroke="#dce7f3" stroke-width="1.2"/>')
        lines.append(f'<text x="{label_x:.2f}" y="{tick_y + 4:.2f}" fill="#9fb3c8" font-size="12" font-family="Helvetica, Arial, sans-serif">{_escape(label)}</text>')


def _three_color_gradient(scale: float, low: str, mid: str, high: str) -> str:
    if scale <= 0.5:
        return _blend_color(low, mid, scale / 0.5 if scale > 0.0 else 0.0)
    return _blend_color(mid, high, (scale - 0.5) / 0.5)


def _blend_color(start: str, stop: str, scale: float) -> str:
    scale = max(0.0, min(1.0, scale))
    s = _parse_hex_color(start)
    t = _parse_hex_color(stop)
    parts = [round(s[index] + (t[index] - s[index]) * scale) for index in range(3)]
    return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _nearest_cell(cells: Sequence[BrusselatorAtlasCell], a_target: float, b_target: float) -> BrusselatorAtlasCell:
    return min(cells, key=lambda cell: abs(cell.a - a_target) + abs(cell.b - b_target))


def _quantile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', '&quot;')
    )
