from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .brusselator_atlas import BrusselatorAtlasCell
from .brusselator_sweep import brusselator_hopf_threshold
from .selkov_atlas import SelkovAtlasCell, selkov_hopf_band


def render_chemical_oscillator_comparison_report(
    brusselator_cells: Sequence[BrusselatorAtlasCell],
    selkov_cells: Sequence[SelkovAtlasCell],
) -> str:
    if not brusselator_cells or not selkov_cells:
        raise ValueError("both cell collections must be non-empty")

    br_anchor = _nearest_brusselator(brusselator_cells, 1.0, 2.4)
    sel_anchor = _nearest_selkov(selkov_cells, 0.08, 0.60)
    sel_band_008 = selkov_hopf_band(0.08)
    sel_band_005 = selkov_hopf_band(0.05)

    br_osc = [cell for cell in brusselator_cells if cell.period is not None]
    sel_osc = [cell for cell in selkov_cells if cell.period is not None]

    lines = [
        "# Chemical oscillator comparison",
        "",
        "This short note compares the two chemistry-facing oscillators now living in `phase-portrait-lab`.",
        "Both models show a Hopf-style bridge from local linearization to a visible long-time cycle, but the parameter geometry is different enough to be worth seeing side by side.",
        "",
        "## 1. Local bifurcation geometry",
        "",
        "### Brusselator",
        "",
        "- equations: `dx/dt = A + x^2 y - (B + 1)x`, `dy/dt = Bx - x^2 y`",
        f"- exact local boundary: `B = 1 + A^2`, so at `A = 1.00` the threshold is `B = {brusselator_hopf_threshold(1.0):.2f}`",
        "- local reading: one smooth curve splits parameter space into a stable side and a one-sided oscillatory side",
        "",
        "### Selkov",
        "",
        "- equations: `dx/dt = -x + a y + x^2 y`, `dy/dt = b - a y - x^2 y`",
        f"- exact local boundaries at `a = 0.05`: `b ∈ ({sel_band_005[0]:.3f}, {sel_band_005[1]:.3f})` is the unstable window",
        f"- exact local boundaries at `a = 0.08`: `b ∈ ({sel_band_008[0]:.3f}, {sel_band_008[1]:.3f})` is the unstable window",
        "- local reading: two Hopf curves create a finite oscillatory band, so the fixed point is stable below the band and stable again above it",
        "",
        "## 2. Global cycle reading on the sampled grids",
        "",
        f"- sampled Brusselator oscillatory cells with measured periods: `{len(br_osc)}`",
        f"- sampled Selkov oscillatory cells with measured periods: `{len(sel_osc)}`",
        f"- Brusselator anchor (`A = {br_anchor.a:.2f}`, `B = {br_anchor.b:.2f}`): `x` amplitude `{br_anchor.x_amplitude:.2f}`, period `{(br_anchor.period or 0.0):.2f}`",
        f"- Selkov anchor (`a = {sel_anchor.a:.3f}`, `b = {sel_anchor.b:.2f}`): `x` amplitude `{sel_anchor.x_amplitude:.2f}`, period `{(sel_anchor.period or 0.0):.2f}`",
        "",
        "## 3. Why the contrast matters",
        "",
        "- the Brusselator atlas is a clean one-threshold story: move far enough above one exact curve and the self-sustained cycle keeps growing",
        "- the Selkov atlas is a finite-band story: oscillation turns on after the lower Hopf edge, but it also turns off again after the upper edge",
        "- together they make the chemistry lane in this repo more honest: Hopf language is shared, but the global parameter geography is model-specific",
        "",
        "## Files to open",
        "",
        "- `assets/brusselator-parameter-atlas.svg`",
        "- `assets/selkov-parameter-atlas.svg`",
        "- `reports/brusselator-parameter-atlas.md`",
        "- `reports/selkov-parameter-atlas.md`",
    ]
    return "\n".join(lines) + "\n"



def write_chemical_oscillator_comparison_report(
    brusselator_cells: Sequence[BrusselatorAtlasCell],
    selkov_cells: Sequence[SelkovAtlasCell],
    output: str | Path,
) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_chemical_oscillator_comparison_report(brusselator_cells, selkov_cells))



def _nearest_brusselator(cells: Sequence[BrusselatorAtlasCell], a_target: float, b_target: float) -> BrusselatorAtlasCell:
    return min(cells, key=lambda cell: abs(cell.a - a_target) + abs(cell.b - b_target))



def _nearest_selkov(cells: Sequence[SelkovAtlasCell], a_target: float, b_target: float) -> SelkovAtlasCell:
    return min(cells, key=lambda cell: abs(cell.a - a_target) + abs(cell.b - b_target))
