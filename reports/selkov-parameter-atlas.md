# Selkov parameter atlas

This report adds a second chemistry-facing oscillator to the repo: the Selkov glycolysis model.

For the Selkov system

```text
dx/dt = -x + a y + x^2 y
dy/dt = b - a y - x^2 y
```

the positive fixed point is `(x*, y*) = (b, b / (a + b^2))` and the Jacobian determinant is exactly `a + b^2`, so the local question is controlled by the trace.
Writing `s = a + b^2`, the trace-zero condition becomes `s^2 - s + 2a = 0`, which yields two exact Hopf boundaries when `a < 1/8`.
That makes the local oscillatory regime a **finite band** in `b` instead of the Brusselator's one-sided region above a single curve.

## Exact local window

- at `a = 0.05`, the exact local oscillatory band is `b ∈ (0.250, 0.915)`
- at `a = 0.08`, the exact local oscillatory band is `b ∈ (0.346, 0.849)`
- at `a = 0.10`, the exact local oscillatory band is `b ∈ (0.420, 0.790)`
- as `a` approaches `1/8`, the two Hopf curves pinch together and the oscillatory band collapses

The generated SVG `assets/selkov-parameter-atlas.svg` keeps the exact local band separate from the numerical long-time cycle measurements.

## What the scan says

- most sampled oscillatory cells stay below about `1.94` in `x` amplitude, with a widest-band extreme near `2.26`
- most measured periods stay below about `20.79`, with an extreme value near `35.26`
- unlike the Brusselator atlas, the Selkov amplitude map fades back to zero on the high-`b` side because the fixed point becomes locally attracting again after the upper Hopf boundary
- the widest and strongest oscillations sit near small `a`, where the exact band is broadest

## Anchor settings

| a | b | local type | x amplitude | y amplitude | period | reading |
| ---: | ---: | --- | ---: | ---: | ---: | --- |
| 0.050 | 0.20 | stable spiral | 0.00 | 0.00 | — | stable fixed point |
| 0.050 | 0.45 | unstable spiral | 0.89 | 1.37 | 13.04 | self-sustained cycle |
| 0.080 | 0.60 | unstable spiral | 0.64 | 0.97 | 9.62 | self-sustained cycle |
| 0.080 | 0.95 | stable spiral | 0.00 | 0.00 | — | stable fixed point |

## Measurement recipe and caveat

The numerical panels use RK4 with `dt = 0.02`, integrate for `240` time units, and measure the final `90` time units.
That is enough to make the stable → oscillatory → stable transition visible on this grid, but it is still a **finite-time** estimate of the cycle size and period.
The point of the atlas is to connect exact Jacobian theory to a visible long-time glycolytic oscillation, not to claim the finite grid is the whole bifurcation theory.
