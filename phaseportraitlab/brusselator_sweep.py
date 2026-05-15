from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .analysis import analyze_fixed_points
from .systems import State, brusselator


@dataclass(frozen=True)
class BrusselatorSweepRow:
    a: float
    b: float
    fixed_point: State
    trace: float
    determinant: float
    discriminant: float
    eigenvalues: tuple[complex, complex]
    classification: str

    @property
    def decay_rate(self) -> float:
        return self.eigenvalues[0].real

    @property
    def oscillation_frequency(self) -> float:
        return abs(self.eigenvalues[0].imag)

    @property
    def hopf_offset(self) -> float:
        return self.b - brusselator_hopf_threshold(self.a)


def brusselator_hopf_threshold(a: float = 1.0) -> float:
    if a <= 0.0:
        raise ValueError("a must be positive")
    return 1.0 + a * a


def sweep_brusselator_b_values(b_values: Sequence[float], *, a: float = 1.0) -> list[BrusselatorSweepRow]:
    rows: list[BrusselatorSweepRow] = []
    for b in b_values:
        item = analyze_fixed_points(brusselator(a=a, b=float(b)))[0]
        rows.append(
            BrusselatorSweepRow(
                a=a,
                b=float(b),
                fixed_point=item.point,
                trace=item.trace,
                determinant=item.determinant,
                discriminant=item.discriminant,
                eigenvalues=item.eigenvalues,
                classification=item.classification,
            )
        )
    return rows


def sweep_brusselator_b_range(*, a: float = 1.0, b_min: float = 1.2, b_max: float = 2.8, steps: int = 17) -> list[BrusselatorSweepRow]:
    if steps < 2:
        raise ValueError("steps must be at least 2")
    if b_max < b_min:
        raise ValueError("b_max must be at least b_min")
    step = (b_max - b_min) / (steps - 1)
    return sweep_brusselator_b_values([b_min + index * step for index in range(steps)], a=a)


def render_brusselator_hopf_sweep(
    rows: Sequence[BrusselatorSweepRow],
    *,
    output: str | Path,
    title: str | None = None,
) -> None:
    if not rows:
        raise ValueError("rows must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    width = 1280
    height = 980
    left = 82.0
    right = 72.0
    top = 128.0
    panel_gap = 42.0
    panel_height = 220.0
    band_height = 110.0
    plot_width = width - left - right

    a = rows[0].a
    threshold = brusselator_hopf_threshold(a)
    b_min = min(row.b for row in rows)
    b_max = max(row.b for row in rows)
    max_abs_trace = max(max(abs(row.trace) for row in rows), 0.1) * 1.18
    max_eigen_scale = max(
        max(abs(row.decay_rate) for row in rows),
        max(row.oscillation_frequency for row in rows),
        0.1,
    ) * 1.18

    def x_for(b: float) -> float:
        if abs(b_max - b_min) < 1e-12:
            return left + plot_width / 2.0
        return left + (b - b_min) / (b_max - b_min) * plot_width

    def y_for_trace(value: float) -> float:
        return top + panel_height / 2.0 - (value / max_abs_trace) * (panel_height / 2.0 - 18.0)

    eigen_top = top + panel_height + panel_gap

    def y_for_eigen(value: float) -> float:
        return eigen_top + panel_height / 2.0 - (value / max_eigen_scale) * (panel_height / 2.0 - 18.0)

    band_top = eigen_top + panel_height + panel_gap
    band_bottom = band_top + band_height

    def polyline(points: Sequence[tuple[float, float]], stroke: str, width_px: float, *, dash: str | None = None) -> str:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
        coords = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
        return f'<polyline fill="none" stroke="{stroke}" stroke-width="{width_px}" stroke-linejoin="round" stroke-linecap="round" points="{coords}"{dash_attr}/>'

    trace_points = [(x_for(row.b), y_for_trace(row.trace)) for row in rows]
    real_points = [(x_for(row.b), y_for_eigen(row.decay_rate)) for row in rows]
    imag_points = [(x_for(row.b), y_for_eigen(row.oscillation_frequency)) for row in rows]
    zero_trace_y = y_for_trace(0.0)
    zero_eigen_y = y_for_eigen(0.0)
    threshold_x = x_for(threshold)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        f'<text x="{left:.0f}" y="54" fill="#e6edf3" font-size="34" font-family="Helvetica, Arial, sans-serif" font-weight="700">{_escape(title or "Brusselator Hopf sweep")}</text>',
        f'<text x="{left:.0f}" y="84" fill="#9fb3c8" font-size="18" font-family="Helvetica, Arial, sans-serif">For A = {a:.1f}, the fixed point stays at x = A while the damping flips sign at B = 1 + A² = {threshold:.2f}.</text>',
    ]

    for panel_top, label, zero_y in (
        (top, 'trace of the Jacobian at the fixed point', zero_trace_y),
        (eigen_top, 'eigenvalue real part versus oscillation frequency', zero_eigen_y),
    ):
        lines.append(f'<rect x="{left:.2f}" y="{panel_top:.2f}" width="{plot_width:.2f}" height="{panel_height:.2f}" rx="18" fill="#122131" stroke="#5e7fa3" stroke-width="2"/>')
        lines.append(f'<text x="{left + 18:.2f}" y="{panel_top + 30:.2f}" fill="#dce7f3" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">{label}</text>')
        lines.append(f'<line x1="{left:.2f}" y1="{zero_y:.2f}" x2="{left + plot_width:.2f}" y2="{zero_y:.2f}" stroke="#334155" stroke-width="1.5" stroke-dasharray="8 6"/>')
        lines.append(f'<line x1="{threshold_x:.2f}" y1="{panel_top + 40:.2f}" x2="{threshold_x:.2f}" y2="{panel_top + panel_height - 18:.2f}" stroke="#fbbf24" stroke-width="2.5" stroke-dasharray="9 7"/>')

    for tick in range(9):
        b_value = b_min + (b_max - b_min) * tick / 8.0
        x = x_for(b_value)
        lines.append(f'<line x1="{x:.2f}" y1="{top + 40:.2f}" x2="{x:.2f}" y2="{band_bottom:.2f}" stroke="#223445" stroke-width="1" opacity="0.7"/>')
        lines.append(f'<text x="{x:.2f}" y="{band_bottom + 24:.2f}" fill="#8aa3bc" font-size="13" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{b_value:.2f}</text>')

    for frac in (-1.0, -0.5, 0.5, 1.0):
        value = frac * max_abs_trace
        y = y_for_trace(value)
        lines.append(f'<text x="{left - 12:.2f}" y="{y + 4:.2f}" fill="#8aa3bc" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{value:.2f}</text>')
    for frac in (-1.0, -0.5, 0.5, 1.0):
        value = frac * max_eigen_scale
        y = y_for_eigen(value)
        lines.append(f'<text x="{left - 12:.2f}" y="{y + 4:.2f}" fill="#8aa3bc" font-size="13" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{value:.2f}</text>')

    lines.append(polyline(trace_points, '#60a5fa', 3.8))
    lines.append(polyline(real_points, '#f97316', 3.4))
    lines.append(polyline(imag_points, '#4ade80', 3.0))

    for row in rows:
        x = x_for(row.b)
        lines.append(f'<circle cx="{x:.2f}" cy="{y_for_trace(row.trace):.2f}" r="5.2" fill="#dbeafe" stroke="#60a5fa" stroke-width="2"/>')
        lines.append(f'<circle cx="{x:.2f}" cy="{y_for_eigen(row.decay_rate):.2f}" r="4.6" fill="#fed7aa" stroke="#f97316" stroke-width="2"/>')
        lines.append(f'<circle cx="{x:.2f}" cy="{y_for_eigen(row.oscillation_frequency):.2f}" r="4.6" fill="#bbf7d0" stroke="#4ade80" stroke-width="2"/>')

    lines.append(f'<rect x="{left:.2f}" y="{band_top:.2f}" width="{plot_width:.2f}" height="{band_height:.2f}" rx="18" fill="#122131" stroke="#5e7fa3" stroke-width="2"/>')
    lines.append(f'<text x="{left + 18:.2f}" y="{band_top + 32:.2f}" fill="#dce7f3" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">local reading of the same fixed point</text>')
    badge_y = band_top + 40.0
    badges = [
        (left + 18.0, 208.0, '#0f2c2a', '#a7f3d0', f'B < {threshold:.2f}: stable spiral'),
        (left + 246.0, 232.0, '#3f2a12', '#fde68a', f'B = {threshold:.2f}: Hopf threshold'),
        (left + 498.0, 244.0, '#32151a', '#fca5a5', f'B > {threshold:.2f}: unstable spiral'),
    ]
    for badge_x, badge_width, fill, text_fill, label in badges:
        lines.append(f'<rect x="{badge_x:.2f}" y="{badge_y:.2f}" width="{badge_width:.2f}" height="24" rx="12" fill="{fill}" opacity="0.96"/>')
        lines.append(f'<text x="{badge_x + 12:.2f}" y="{badge_y + 16:.2f}" fill="{text_fill}" font-size="13" font-family="Helvetica, Arial, sans-serif">{label}</text>')
    lines.append(f'<text x="{left + 18:.2f}" y="{band_top + 84:.2f}" fill="#dce7f3" font-size="15" font-family="Helvetica, Arial, sans-serif">The imaginary part stays near one, so the turning tendency remains visible while the real part decides damping versus growth.</text>')
    lines.append(f'<text x="{left + 18:.2f}" y="{band_top + 106:.2f}" fill="#dce7f3" font-size="15" font-family="Helvetica, Arial, sans-serif">That is the local bridge from a calm fixed point to a self-sustained oscillation.</text>')

    sample_rows = sweep_brusselator_b_values([1.6, threshold, 2.4], a=a)
    callout_x = width - 320.0
    callout_y = 154.0
    lines.append(f'<rect x="{callout_x:.2f}" y="{callout_y:.2f}" width="250" height="184" rx="18" fill="#0b1722" stroke="#5e7fa3" stroke-width="1.7"/>')
    lines.append(f'<text x="{callout_x + 20:.2f}" y="{callout_y + 30:.2f}" fill="#dce7f3" font-size="18" font-family="Helvetica, Arial, sans-serif" font-weight="700">Three anchor settings</text>')
    for index, row in enumerate(sample_rows):
        eig = row.eigenvalues[0]
        sign = '+' if eig.imag >= 0 else '-'
        y = callout_y + 60.0 + index * 42.0
        lines.append(f'<text x="{callout_x + 20:.2f}" y="{y:.2f}" fill="#dce7f3" font-size="15" font-family="Helvetica, Arial, sans-serif">B = {row.b:.2f} → {row.classification}</text>')
        lines.append(f'<text x="{callout_x + 36:.2f}" y="{y + 20:.2f}" fill="#9fb3c8" font-size="13" font-family="Helvetica, Arial, sans-serif">λ = {eig.real:.2f}{sign}{abs(eig.imag):.2f}i at (x*, y*) = ({row.fixed_point[0]:.1f}, {row.fixed_point[1]:.1f})</text>')

    legend_y = height - 46.0
    lines.append(f'<line x1="{left:.2f}" y1="{legend_y:.2f}" x2="{left + 28:.2f}" y2="{legend_y:.2f}" stroke="#60a5fa" stroke-width="4"/><text x="{left + 40:.2f}" y="{legend_y + 5:.2f}" fill="#dce7f3" font-size="14" font-family="Helvetica, Arial, sans-serif">trace</text>')
    lines.append(f'<line x1="{left + 130:.2f}" y1="{legend_y:.2f}" x2="{left + 158:.2f}" y2="{legend_y:.2f}" stroke="#f97316" stroke-width="4"/><text x="{left + 170:.2f}" y="{legend_y + 5:.2f}" fill="#dce7f3" font-size="14" font-family="Helvetica, Arial, sans-serif">Re(λ)</text>')
    lines.append(f'<line x1="{left + 250:.2f}" y1="{legend_y:.2f}" x2="{left + 278:.2f}" y2="{legend_y:.2f}" stroke="#4ade80" stroke-width="4"/><text x="{left + 290:.2f}" y="{legend_y + 5:.2f}" fill="#dce7f3" font-size="14" font-family="Helvetica, Arial, sans-serif">|Im(λ)|</text>')
    lines.append(f'<line x1="{left + 392:.2f}" y1="{legend_y - 10:.2f}" x2="{left + 392:.2f}" y2="{legend_y + 10:.2f}" stroke="#fbbf24" stroke-width="3" stroke-dasharray="9 7"/><text x="{left + 406:.2f}" y="{legend_y + 5:.2f}" fill="#dce7f3" font-size="14" font-family="Helvetica, Arial, sans-serif">Hopf threshold B = {threshold:.2f}</text>')
    lines.append('</svg>')

    output.write_text('\n'.join(lines) + '\n')


def render_brusselator_hopf_report(rows: Sequence[BrusselatorSweepRow]) -> str:
    if not rows:
        raise ValueError("rows must not be empty")

    a = rows[0].a
    threshold = brusselator_hopf_threshold(a)
    header = [
        '# Brusselator Hopf sweep',
        '',
        f'This report tracks the Brusselator fixed point while `A = {a:.1f}` stays fixed and `B` moves through the Hopf threshold `B = 1 + A^2 = {threshold:.2f}`.',
        '',
        'At the fixed point `(x*, y*) = (A, B / A)`, the Jacobian is',
        '',
        '```text',
        '[ B - 1    A^2 ]',
        '[  -B     -A^2 ]',
        '```',
        '',
        f'so the trace is `B - 1 - A^2 = B - {threshold:.2f}` and the determinant is `A^2 = {a * a:.2f}`.',
        '',
        '## Sampled sweep',
        '',
        '| B | fixed point | trace | Re(λ) | Im(λ) magnitude | local type |',
        '| --- | --- | ---: | ---: | ---: | --- |',
    ]
    body = [
        f'| {row.b:.2f} | ({row.fixed_point[0]:.2f}, {row.fixed_point[1]:.2f}) | {row.trace:.3f} | {row.decay_rate:.3f} | {row.oscillation_frequency:.3f} | {row.classification} |'
        for row in rows
    ]
    footer = [
        '',
        '## Reading the sweep',
        '',
        f'- for `B < {threshold:.2f}`, the real part is negative, so perturbations spiral inward',
        f'- at `B = {threshold:.2f}`, the trace hits zero and the linearization lands on the Hopf boundary',
        f'- for `B > {threshold:.2f}`, the real part turns positive, so the fixed point repels while oscillatory structure remains',
        '- the generated SVG in `assets/brusselator-hopf-sweep.svg` puts the trace, eigenvalue drift, and local reading on one card',
    ]
    return '\n'.join(header + body + footer) + '\n'


def write_brusselator_hopf_report(rows: Sequence[BrusselatorSweepRow], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_brusselator_hopf_report(rows))


def _escape(text: str) -> str:
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )
