from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .brusselator_atlas import BrusselatorAtlasCell
from .brusselator_sweep import brusselator_hopf_threshold
from .selkov_atlas import SelkovAtlasCell, selkov_hopf_band


def render_chemistry_local_global_report(
    brusselator_cells: Sequence[BrusselatorAtlasCell],
    selkov_cells: Sequence[SelkovAtlasCell],
) -> str:
    if not brusselator_cells or not selkov_cells:
        raise ValueError("both cell collections must be non-empty")

    br_below = _nearest_brusselator(brusselator_cells, 1.0, 1.6)
    br_near = _nearest_brusselator(brusselator_cells, 1.0, 2.1)
    br_far = _nearest_brusselator(brusselator_cells, 1.0, 2.4)

    sel_below = _nearest_selkov(selkov_cells, 0.08, 0.25)
    sel_edge = _nearest_selkov(selkov_cells, 0.08, 0.35)
    sel_mid = _nearest_selkov(selkov_cells, 0.08, 0.60)
    sel_above = _nearest_selkov(selkov_cells, 0.08, 0.95)
    sel_band = selkov_hopf_band(0.08)
    assert sel_band is not None

    lines = [
        "# Local versus global chemistry",
        "",
        "This note is the bridge between the Jacobian-based chemistry reports and the longer-time orbit measurements in `phase-portrait-lab`.",
        "The question is narrow: **what does local linearization tell us exactly, and what only appears once we actually integrate the trajectories?**",
        "",
        "## 1. The split to keep in mind",
        "",
        "Local analysis is about the fixed point itself.",
        "It tells us whether tiny perturbations decay, hover, or grow near that point.",
        "For the two chemistry models in this repo, that part is exact once the Jacobian is written down.",
        "",
        "Global measurement starts one step later.",
        "Once the fixed point is not locally attracting, we still need to ask what the finite orbit actually does on the scanned parameter grid:",
        "",
        "- does it settle back to the fixed point,",
        "- does it grow into a visible limit cycle,",
        "- how large is that cycle,",
        "- and how long is one turn?",
        "",
        "The Jacobian does **not** answer the amplitude or period questions by itself.",
        "That is why the repo keeps the exact local layer separate from the RK4 tail measurements.",
        "",
        "## 2. Brusselator: one threshold, then a growing cycle",
        "",
        "For the Brusselator, the positive fixed point is `(x*, y*) = (A, B / A)` and the exact local Hopf boundary is",
        "",
        "```text",
        "B = 1 + A^2",
        "```",
        "",
        f"At `A = 1.00`, that threshold is `B = {brusselator_hopf_threshold(1.0):.2f}`.",
        "Below it the fixed point attracts. Above it the fixed point repels and the numerical scan picks up a self-sustained cycle.",
        "",
        "| A | B | trace | local type | x amplitude | period | reading |",
        "| ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for cell, reading in [
        (br_below, "locally damped fixed point"),
        (br_near, "just above threshold: small but real cycle"),
        (br_far, "deeper on the oscillatory side"),
    ]:
        lines.append(
            f"| {cell.a:.2f} | {cell.b:.2f} | {cell.trace:.3f} | {cell.classification} | {cell.x_amplitude:.2f} | {_period_text(cell.period)} | {reading} |"
        )

    lines.extend(
        [
            "",
            "The useful lesson is not just that the trace changes sign.",
            "It is that a **small positive trace** near the Hopf curve already corresponds to a visible but still modest cycle, while farther above the threshold the cycle is much larger.",
            "Local theory marks the onset. The orbit measurement shows the scale.",
            "",
            "## 3. Selkov: a finite oscillatory band, not a half-plane",
            "",
            "The Selkov model keeps the same local-versus-global split, but the parameter geometry changes.",
            "For `a = 0.08`, the exact unstable band from the Jacobian is",
            "",
            "```text",
            f"{sel_band[0]:.3f} < b < {sel_band[1]:.3f}",
            "```",
            "",
            "So the fixed point is stable below the lower Hopf edge, unstable inside the band, and stable again above the upper edge.",
            "That already tells us something global-looking about the map of parameter space, but it still does not tell us how large or slow the cycle becomes in the middle of the band.",
            "",
            "| a | b | trace | local type | x amplitude | period | reading |",
            "| ---: | ---: | ---: | --- | ---: | ---: | --- |",
        ]
    )
    for cell, reading in [
        (sel_below, "below the band: fixed point attracts"),
        (sel_edge, "just inside the band: tiny cycle"),
        (sel_mid, "middle of the band: strong cycle"),
        (sel_above, "above the band: attraction returns"),
    ]:
        lines.append(
            f"| {cell.a:.3f} | {cell.b:.2f} | {cell.trace:.3f} | {cell.classification} | {cell.x_amplitude:.2f} | {_period_text(cell.period)} | {reading} |"
        )

    lines.extend(
        [
            "",
            "This is the clearest contrast with the Brusselator.",
            "The Jacobian does not just say *oscillatory or not*; it says the unstable zone is **bounded**.",
            "Then the numerical layer shows how that bounded zone still contains very different cycle sizes depending on where you stand inside it.",
            "",
            "## 4. Where the Jacobian stops being enough",
            "",
            "The local Jacobian is enough for:",
            "",
            "- exact Hopf thresholds in these two models,",
            "- local classification of the fixed point,",
            "- the sign change that tells us where attraction gives way to repulsion.",
            "",
            "It is **not** enough for:",
            "",
            "- the finite amplitude of the limit cycle,",
            "- the cycle period on the sampled grid,",
            "- how quickly the orbit reaches that cycle,",
            "- or whether a finite-time scan is still too close to threshold to give a clean measurement.",
            "",
            "That is why the chemistry lane in this repo now has two layers:",
            "",
            "1. exact local boundaries from the Jacobian,",
            "2. finite-time orbit measurements that make the long-time motion visible without pretending to replace full bifurcation theory.",
            "",
            "## 5. Open next",
            "",
            "- `assets/brusselator-parameter-atlas.svg`",
            "- `assets/selkov-parameter-atlas.svg`",
            "- `reports/brusselator-parameter-atlas.md`",
            "- `reports/selkov-parameter-atlas.md`",
            "- `notebooks/chemistry_local_to_global.ipynb`",
            "",
            "## Caveat",
            "",
            "All amplitude and period numbers in this note come from finite RK4 runs on a fixed grid.",
            "They are here to show the bridge from local stability to visible oscillation, not to claim an exhaustive bifurcation survey.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_chemistry_local_global_report(
    brusselator_cells: Sequence[BrusselatorAtlasCell],
    selkov_cells: Sequence[SelkovAtlasCell],
    output: str | Path,
) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_chemistry_local_global_report(brusselator_cells, selkov_cells))


def _period_text(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def _nearest_brusselator(cells: Sequence[BrusselatorAtlasCell], a_target: float, b_target: float) -> BrusselatorAtlasCell:
    return min(cells, key=lambda cell: abs(cell.a - a_target) + abs(cell.b - b_target))


def _nearest_selkov(cells: Sequence[SelkovAtlasCell], a_target: float, b_target: float) -> SelkovAtlasCell:
    return min(cells, key=lambda cell: abs(cell.a - a_target) + abs(cell.b - b_target))
