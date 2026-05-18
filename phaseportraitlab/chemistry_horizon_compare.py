from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Sequence

from .brusselator_atlas import estimate_brusselator_cycle_metrics
from .brusselator_sweep import brusselator_hopf_threshold
from .selkov_atlas import estimate_selkov_cycle_metrics, selkov_hopf_band


@dataclass(frozen=True)
class HorizonComparisonRow:
    model: str
    a: float
    b: float
    edge_distance: float
    short_settle_time: float
    short_sample_time: float
    short_x_amplitude: float
    short_period: float | None
    short_peak_count: int
    long_settle_time: float
    long_sample_time: float
    long_x_amplitude: float
    long_period: float | None
    long_peak_count: int

    @property
    def amplitude_gap(self) -> float:
        return self.short_x_amplitude - self.long_x_amplitude

    @property
    def period_gap(self) -> float:
        if self.short_period is None or self.long_period is None:
            return 0.0
        return abs(self.short_period - self.long_period)


def build_brusselator_horizon_rows(
    *,
    a: float = 1.0,
    offsets: Sequence[float] = (0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.28),
    short_settle_time: float = 20.0,
    short_sample_time: float = 30.0,
    long_settle_time: float = 180.0,
    long_sample_time: float = 90.0,
) -> list[HorizonComparisonRow]:
    if not offsets:
        raise ValueError("offsets must not be empty")
    threshold = brusselator_hopf_threshold(a)
    rows: list[HorizonComparisonRow] = []
    for offset in offsets:
        b = threshold + float(offset)
        short = estimate_brusselator_cycle_metrics(a, b, settle_time=short_settle_time, sample_time=short_sample_time)
        long = estimate_brusselator_cycle_metrics(a, b, settle_time=long_settle_time, sample_time=long_sample_time)
        rows.append(
            HorizonComparisonRow(
                model="Brusselator",
                a=a,
                b=b,
                edge_distance=float(offset),
                short_settle_time=short_settle_time,
                short_sample_time=short_sample_time,
                short_x_amplitude=short.x_amplitude,
                short_period=short.period,
                short_peak_count=short.peak_count,
                long_settle_time=long_settle_time,
                long_sample_time=long_sample_time,
                long_x_amplitude=long.x_amplitude,
                long_period=long.period,
                long_peak_count=long.peak_count,
            )
        )
    return rows


def build_selkov_horizon_rows(
    *,
    a: float = 0.08,
    offsets: Sequence[float] = (0.003, 0.005, 0.008, 0.012, 0.02, 0.04, 0.08, 0.16),
    short_settle_time: float = 40.0,
    short_sample_time: float = 45.0,
    long_settle_time: float = 240.0,
    long_sample_time: float = 120.0,
) -> list[HorizonComparisonRow]:
    if not offsets:
        raise ValueError("offsets must not be empty")
    band = selkov_hopf_band(a)
    if band is None:
        raise ValueError("chosen a has no oscillatory band")
    lower_edge = band[0]
    rows: list[HorizonComparisonRow] = []
    for offset in offsets:
        b = lower_edge + float(offset)
        short = estimate_selkov_cycle_metrics(a, b, settle_time=short_settle_time, sample_time=short_sample_time)
        long = estimate_selkov_cycle_metrics(a, b, settle_time=long_settle_time, sample_time=long_sample_time)
        rows.append(
            HorizonComparisonRow(
                model="Selkov",
                a=a,
                b=b,
                edge_distance=float(offset),
                short_settle_time=short_settle_time,
                short_sample_time=short_sample_time,
                short_x_amplitude=short.x_amplitude,
                short_period=short.period,
                short_peak_count=short.peak_count,
                long_settle_time=long_settle_time,
                long_sample_time=long_sample_time,
                long_x_amplitude=long.x_amplitude,
                long_period=long.period,
                long_peak_count=long.peak_count,
            )
        )
    return rows


def _text(x: float, y: float, content: str, *, size: int = 16, fill: str = "#dce7f3", anchor: str = "start", weight: str = "normal") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" text-anchor="{anchor}" font-family="Helvetica, Arial, sans-serif" font-weight="{weight}">{escape(content)}</text>'


def _line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#31465d", width: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width:.1f}"{dash_attr}/>'


def _polyline(points: list[tuple[float, float]], *, stroke: str, width: float = 3.0) -> str:
    payload = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline fill="none" stroke="{stroke}" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="round" points="{payload}"/>'


def _circle(x: float, y: float, *, r: float = 4.0, fill: str = "#f97316") -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'


def render_chemistry_horizon_compare_svg(
    brusselator_rows: Sequence[HorizonComparisonRow],
    selkov_rows: Sequence[HorizonComparisonRow],
    *,
    output: str | Path,
    title: str = "Near-threshold chemistry: amplitude settles slower than period",
) -> None:
    if not brusselator_rows or not selkov_rows:
        raise ValueError("comparison rows must not be empty")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    width = 1380
    height = 1500
    margin_left = 70.0
    margin_right = 56.0
    panel_w = 592.0
    panel_h = 320.0
    col_gap = 70.0
    top_row_y = 144.0
    bottom_row_y = 536.0
    left_x = margin_left
    right_x = left_x + panel_w + col_gap
    short_color = "#f97316"
    long_color = "#38bdf8"

    def draw_panel(
        rows: Sequence[HorizonComparisonRow],
        *,
        left: float,
        top: float,
        value_key: str,
        label: str,
        subtitle: str,
        x_label: str,
        note: str,
    ) -> list[str]:
        x0 = left + 64.0
        x1 = left + panel_w - 24.0
        y0 = top + 72.0
        y1 = top + panel_h - 54.0
        x_min = min(row.edge_distance for row in rows)
        x_max = max(row.edge_distance for row in rows)
        short_values = [getattr(row, f"short_{value_key}") or 0.0 for row in rows]
        long_values = [getattr(row, f"long_{value_key}") or 0.0 for row in rows]
        y_max = max(short_values + long_values) * 1.12
        y_min = 0.0

        def map_x(value: float) -> float:
            return x0 + (value - x_min) / max(x_max - x_min, 1e-9) * (x1 - x0)

        def map_y(value: float) -> float:
            return y1 - (value - y_min) / max(y_max - y_min, 1e-9) * (y1 - y0)

        parts = [
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{panel_w:.1f}" height="{panel_h:.1f}" rx="20" fill="#122131" stroke="#58708c" stroke-width="1.8"/>',
            _text(left + 18.0, top + 30.0, label, size=20, weight="700"),
            _text(left + 18.0, top + 54.0, subtitle, size=13, fill="#9fb3c8"),
        ]
        for step in range(6):
            frac = step / 5
            y = y0 + frac * (y1 - y0)
            value = y_max - frac * (y_max - y_min)
            parts.append(_line(x0, y, x1, y, stroke="#24384b", dash="4 6"))
            fmt = f"{value:.2f}" if y_max < 20 else f"{value:.1f}"
            parts.append(_text(x0 - 10.0, y + 4.0, fmt, size=12, fill="#9fb3c8", anchor="end"))
        for step in range(6):
            frac = step / 5
            x = x0 + frac * (x1 - x0)
            value = x_min + frac * (x_max - x_min)
            parts.append(_line(x, y0, x, y1, stroke="#1e3144", dash="4 6"))
            parts.append(_text(x, y1 + 24.0, f"{value:.3f}" if x_max < 0.2 else f"{value:.2f}", size=12, fill="#9fb3c8", anchor="middle"))
        parts.append(_line(x0, y0, x0, y1, stroke="#89a2bc", width=2.0))
        parts.append(_line(x0, y1, x1, y1, stroke="#89a2bc", width=2.0))
        short_points = [(map_x(row.edge_distance), map_y(getattr(row, f"short_{value_key}") or 0.0)) for row in rows]
        long_points = [(map_x(row.edge_distance), map_y(getattr(row, f"long_{value_key}") or 0.0)) for row in rows]
        parts.append(_polyline(short_points, stroke=short_color))
        parts.append(_polyline(long_points, stroke=long_color))
        for x, y in short_points:
            parts.append(_circle(x, y, fill=short_color))
        for x, y in long_points:
            parts.append(_circle(x, y, fill=long_color))
        parts.append(_text((x0 + x1) / 2.0, y1 + 48.0, x_label, size=14, anchor="middle"))
        parts.append(_text(left + 20.0, top + panel_h - 16.0, note, size=12, fill="#c8d6e5"))
        return parts

    lead_bruss = brusselator_rows[0]
    lead_selkov = selkov_rows[0]
    bruss_far = brusselator_rows[-1]
    selkov_far = selkov_rows[-1]
    max_period_gap = max(row.period_gap for row in list(brusselator_rows) + list(selkov_rows))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '</defs>',
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        _text(margin_left, 52.0, title, size=34, weight="700"),
        _text(margin_left, 82.0, "The Hopf boundary is exact. The newborn cycle size is not. Short settle windows overstate amplitude long before they noticeably move the period.", size=16, fill="#9fb3c8"),
        f'<rect x="{margin_left:.1f}" y="96.0" width="280.0" height="24.0" rx="12" fill="#122131" stroke="#58708c" stroke-width="1.0"/>',
        _line(margin_left + 18.0, 108.0, margin_left + 52.0, 108.0, stroke=short_color, width=4.0),
        _text(margin_left + 62.0, 113.0, "short horizon", size=13),
        _line(margin_left + 154.0, 108.0, margin_left + 188.0, 108.0, stroke=long_color, width=4.0),
        _text(margin_left + 198.0, 113.0, "long horizon", size=13),
    ]

    parts.extend(
        draw_panel(
            brusselator_rows,
            left=left_x,
            top=top_row_y,
            value_key="x_amplitude",
            label="Brusselator x-amplitude near B = 1 + A²",
            subtitle="A = 1.00; short and long horizons tell different stories right after onset",
            x_label="ΔB above the Hopf curve",
            note=f"At ΔB={lead_bruss.edge_distance:.2f}, the short horizon adds {lead_bruss.amplitude_gap:.2f} of extra x-amplitude; by ΔB={bruss_far.edge_distance:.2f}, the gap is {bruss_far.amplitude_gap:.2f}.",
        )
    )
    parts.extend(
        draw_panel(
            selkov_rows,
            left=right_x,
            top=top_row_y,
            value_key="x_amplitude",
            label="Selkov x-amplitude just inside the lower Hopf edge",
            subtitle="a = 0.08; the same finite-time bias shows up inside the oscillatory band",
            x_label="Δb above the lower Hopf edge",
            note=f"At Δb={lead_selkov.edge_distance:.3f}, the short horizon adds {lead_selkov.amplitude_gap:.2f} of extra x-amplitude; by Δb={selkov_far.edge_distance:.2f}, the gap is {selkov_far.amplitude_gap:.2f}.",
        )
    )
    parts.extend(
        draw_panel(
            brusselator_rows,
            left=left_x,
            top=bottom_row_y,
            value_key="period",
            label="Brusselator period is already stable",
            subtitle="The two period curves almost overlap while amplitude is still settling",
            x_label="ΔB above the Hopf curve",
            note=f"Maximum period gap across both models in this card: {max_period_gap:.3f} time units.",
        )
    )
    parts.extend(
        draw_panel(
            selkov_rows,
            left=right_x,
            top=bottom_row_y,
            value_key="period",
            label="Selkov period settles before amplitude does",
            subtitle="Near threshold, period shifts a little while amplitude shifts much more",
            x_label="Δb above the lower Hopf edge",
            note="A single fixed scan can locate onset before it can trust the newborn cycle size.",
        )
    )

    summary_y = 948.0
    parts.append(f'<rect x="{margin_left:.1f}" y="{summary_y:.1f}" width="{width - margin_left - margin_right:.1f}" height="146.0" rx="18" fill="#0d1722" stroke="#58708c" stroke-width="1.2"/>')
    parts.append(_text(margin_left + 18.0, summary_y + 28.0, "Read the card like this", size=18, weight="700"))
    parts.append(_text(margin_left + 18.0, summary_y + 54.0, f"• Brusselator: at ΔB={lead_bruss.edge_distance:.2f}, x-amplitude falls from {lead_bruss.short_x_amplitude:.2f} on the short horizon to {lead_bruss.long_x_amplitude:.2f} on the long one, while period only shifts from {lead_bruss.short_period:.2f} to {lead_bruss.long_period:.2f}.", size=14, fill="#c8d6e5"))
    parts.append(_text(margin_left + 18.0, summary_y + 78.0, f"• Selkov: at Δb={lead_selkov.edge_distance:.3f}, x-amplitude falls from {lead_selkov.short_x_amplitude:.2f} to {lead_selkov.long_x_amplitude:.2f}, with period moving only from {lead_selkov.short_period:.2f} to {lead_selkov.long_period:.2f}.", size=14, fill="#c8d6e5"))
    parts.append(_text(margin_left + 18.0, summary_y + 102.0, "• The threshold tells you where oscillation begins. The finite cycle size near that threshold still needs enough settling time.", size=14, fill="#c8d6e5"))
    parts.append('</svg>')
    output.write_text("\n".join(parts) + "\n")


def render_chemistry_horizon_compare_report(
    brusselator_rows: Sequence[HorizonComparisonRow],
    selkov_rows: Sequence[HorizonComparisonRow],
) -> str:
    if not brusselator_rows or not selkov_rows:
        raise ValueError("comparison rows must not be empty")

    bruss_lead = brusselator_rows[0]
    bruss_far = brusselator_rows[-1]
    selkov_lead = selkov_rows[0]
    selkov_far = selkov_rows[-1]
    max_period_gap = max(row.period_gap for row in list(brusselator_rows) + list(selkov_rows))
    bruss_far_gap = max(0.0, bruss_far.amplitude_gap)
    selkov_far_gap = max(0.0, selkov_far.amplitude_gap)

    lines = [
        "# Chemistry horizon convergence sidecar",
        "",
        "This pass asks one bounded question: **if the Jacobian already told us where oscillation begins, how much does a longer integration horizon still change the measured newborn cycle?**",
        "",
        "The answer in both chemistry models is the same in spirit:",
        "",
        "- near threshold, a short settle window makes the x-amplitude look too large",
        "- the period is much less sensitive over the same range",
        "- farther from threshold, the two horizons nearly agree",
        "",
        "## Brusselator anchor",
        "",
        f"At `A = {bruss_lead.a:.2f}`, the exact Hopf edge is `B = 1 + A^2 = {bruss_lead.b - bruss_lead.edge_distance:.2f}`.",
        f"At the smallest sampled offset `ΔB = {bruss_lead.edge_distance:.2f}`, the short horizon gives `x amplitude = {bruss_lead.short_x_amplitude:.3f}` while the long horizon gives `{bruss_lead.long_x_amplitude:.3f}`. The period only moves from `{bruss_lead.short_period:.3f}` to `{bruss_lead.long_period:.3f}`.",
        f"By `ΔB = {bruss_far.edge_distance:.2f}`, the amplitude gap has collapsed to `{bruss_far_gap:.3f}`.",
        "",
        "## Selkov anchor",
        "",
        f"At `a = {selkov_lead.a:.3f}`, the lower Hopf edge sits at `b ≈ {selkov_lead.b - selkov_lead.edge_distance:.3f}`.",
        f"At the smallest sampled offset `Δb = {selkov_lead.edge_distance:.3f}`, the short horizon gives `x amplitude = {selkov_lead.short_x_amplitude:.3f}` while the long horizon gives `{selkov_lead.long_x_amplitude:.3f}`. The period only moves from `{selkov_lead.short_period:.3f}` to `{selkov_lead.long_period:.3f}`.",
        f"By `Δb = {selkov_far.edge_distance:.3f}`, the amplitude gap has collapsed to `{selkov_far_gap:.3f}`.",
        "",
        "## What this changes in the repo story",
        "",
        "The local-versus-global note already said that the Jacobian does not give amplitude or period by itself.",
        "This sidecar tightens that claim: even once we do integrate the orbit, a finite scan horizon can still make the brand-new cycle look larger than it really is, while the period is already almost settled.",
        "",
        f"Across this card, the largest period shift between the short and long horizons is only `{max_period_gap:.3f}` time units.",
        "",
        "## Open next",
        "",
        "- `assets/chemistry-horizon-convergence.svg`",
        "- `assets/chemistry-horizon-convergence.png`",
        "- `assets/chemistry-horizon-convergence.csv`",
        "- `reports/chemistry-horizon-convergence.md`",
        "- `notebooks/chemistry_horizon_convergence.ipynb`",
    ]
    return "\n".join(lines) + "\n"


def write_chemistry_horizon_compare_report(
    brusselator_rows: Sequence[HorizonComparisonRow],
    selkov_rows: Sequence[HorizonComparisonRow],
    output: str | Path,
) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_chemistry_horizon_compare_report(brusselator_rows, selkov_rows))


def export_png_from_svg(svg_path: str | Path, png_path: str | Path, *, size: int = 2200, dpi: int = 300) -> bool:
    svg_file = Path(svg_path).resolve()
    png_file = Path(png_path).resolve()
    qlmanage = shutil.which("qlmanage")
    if qlmanage is None:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [qlmanage, "-t", "-s", str(size), "-o", tmpdir, str(svg_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        generated = Path(tmpdir) / f"{svg_file.name}.png"
        if not generated.exists():
            raise FileNotFoundError(f"Quick Look did not generate {generated}")
        png_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated, png_file)

    sips = shutil.which("sips")
    if sips is not None:
        subprocess.run(
            [sips, "--setProperty", "dpiWidth", str(dpi), "--setProperty", "dpiHeight", str(dpi), str(png_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return True
