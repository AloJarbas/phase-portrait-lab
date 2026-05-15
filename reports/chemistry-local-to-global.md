# Local versus global chemistry

This note is the bridge between the Jacobian-based chemistry reports and the longer-time orbit measurements in `phase-portrait-lab`.
The question is narrow: **what does local linearization tell us exactly, and what only appears once we actually integrate the trajectories?**

## 1. The split to keep in mind

Local analysis is about the fixed point itself.
It tells us whether tiny perturbations decay, hover, or grow near that point.
For the two chemistry models in this repo, that part is exact once the Jacobian is written down.

Global measurement starts one step later.
Once the fixed point is not locally attracting, we still need to ask what the finite orbit actually does on the scanned parameter grid:

- does it settle back to the fixed point,
- does it grow into a visible limit cycle,
- how large is that cycle,
- and how long is one turn?

The Jacobian does **not** answer the amplitude or period questions by itself.
That is why the repo keeps the exact local layer separate from the RK4 tail measurements.

## 2. Brusselator: one threshold, then a growing cycle

For the Brusselator, the positive fixed point is `(x*, y*) = (A, B / A)` and the exact local Hopf boundary is

```text
B = 1 + A^2
```

At `A = 1.00`, that threshold is `B = 2.00`.
Below it the fixed point attracts. Above it the fixed point repels and the numerical scan picks up a self-sustained cycle.

| A | B | trace | local type | x amplitude | period | reading |
| ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0.95 | 1.56 | -0.347 | stable spiral | 0.00 | — | locally damped fixed point |
| 0.95 | 2.11 | 0.209 | unstable spiral | 0.56 | 6.71 | just above threshold: small but real cycle |
| 0.95 | 2.39 | 0.486 | unstable spiral | 0.97 | 6.91 | deeper on the oscillatory side |

The useful lesson is not just that the trace changes sign.
It is that a **small positive trace** near the Hopf curve already corresponds to a visible but still modest cycle, while farther above the threshold the cycle is much larger.
Local theory marks the onset. The orbit measurement shows the scale.

## 3. Selkov: a finite oscillatory band, not a half-plane

The Selkov model keeps the same local-versus-global split, but the parameter geometry changes.
For `a = 0.08`, the exact unstable band from the Jacobian is

```text
0.346 < b < 0.849
```

So the fixed point is stable below the lower Hopf edge, unstable inside the band, and stable again above the upper edge.
That already tells us something global-looking about the map of parameter space, but it still does not tell us how large or slow the cycle becomes in the middle of the band.

| a | b | trace | local type | x amplitude | period | reading |
| ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0.080 | 0.25 | -0.265 | stable spiral | 0.00 | — | below the band: fixed point attracts |
| 0.080 | 0.35 | 0.007 | unstable spiral | 0.08 | 14.02 | just inside the band: tiny cycle |
| 0.080 | 0.60 | 0.196 | unstable spiral | 0.64 | 9.62 | middle of the band: strong cycle |
| 0.080 | 0.95 | -0.145 | stable spiral | 0.00 | — | above the band: attraction returns |

This is the clearest contrast with the Brusselator.
The Jacobian does not just say *oscillatory or not*; it says the unstable zone is **bounded**.
Then the numerical layer shows how that bounded zone still contains very different cycle sizes depending on where you stand inside it.

## 4. Where the Jacobian stops being enough

The local Jacobian is enough for:

- exact Hopf thresholds in these two models,
- local classification of the fixed point,
- the sign change that tells us where attraction gives way to repulsion.

It is **not** enough for:

- the finite amplitude of the limit cycle,
- the cycle period on the sampled grid,
- how quickly the orbit reaches that cycle,
- or whether a finite-time scan is still too close to threshold to give a clean measurement.

That is why the chemistry lane in this repo now has two layers:

1. exact local boundaries from the Jacobian,
2. finite-time orbit measurements that make the long-time motion visible without pretending to replace full bifurcation theory.

## 5. Open next

- `assets/brusselator-parameter-atlas.svg`
- `assets/selkov-parameter-atlas.svg`
- `reports/brusselator-parameter-atlas.md`
- `reports/selkov-parameter-atlas.md`
- `notebooks/chemistry_local_to_global.ipynb`

## Caveat

All amplitude and period numbers in this note come from finite RK4 runs on a fixed grid.
They are here to show the bridge from local stability to visible oscillation, not to claim an exhaustive bifurcation survey.
