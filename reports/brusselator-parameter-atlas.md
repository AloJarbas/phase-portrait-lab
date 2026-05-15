# Brusselator parameter atlas

This report extends the one-parameter Hopf sweep into a two-parameter chemistry map.

For the Brusselator

```text
dx/dt = A + x^2 y - (B + 1)x
dy/dt = Bx - x^2 y
```

the fixed point stays at `(x*, y*) = (A, B / A)` and the Jacobian trace is exactly `B - 1 - A^2`.
So the Hopf curve is `B = 1 + A^2`: below it the fixed point is a stable spiral; above it the fixed point repels and a self-sustained cycle appears.

The generated SVG `assets/brusselator-parameter-atlas.svg` keeps those two readings separate:

- the top panel is exact local theory from the Jacobian
- the middle panel adds a numerical estimate of long-time `x` amplitude
- the bottom panel adds a numerical period estimate from peak spacing

## What the scan says

- most unstable sampled cells stay below about `6.66` in `x` amplitude, while the far low-`A` / high-`B` corner stretches out to `13.66`
- most measured periods stay below about `19.43`, with an extreme corner value near `27.27`
- larger `A` values move the Hopf curve upward while also shortening the cycle period for comparable positive offsets above threshold
- below threshold the report sets the oscillation amplitude to zero on purpose: the exact local theory says the fixed point attracts there, even if finite-time transients can decay slowly near the boundary

## Anchor settings

| A | B | Δ = B - (1 + A²) | local type | x amplitude | y amplitude | period | reading |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 0.83 | 1.28 | -0.42 | stable spiral | 0.00 | 0.00 | — | stable fixed point |
| 0.83 | 2.11 | +0.42 | unstable spiral | 0.83 | 1.13 | 7.89 | self-sustained cycle |
| 0.95 | 2.39 | +0.49 | unstable spiral | 0.97 | 1.23 | 6.91 | self-sustained cycle |
| 1.53 | 3.50 | +0.15 | unstable spiral | 0.61 | 0.71 | 4.21 | self-sustained cycle |
| 2.00 | 5.44 | +0.44 | unstable spiral | 1.49 | 1.58 | 3.83 | self-sustained cycle |

## Measurement recipe and caveat

The numerical panels use RK4 with `dt = 0.015`, integrate for `180` time units, and measure the final `75` time units.
That is enough to make the post-Hopf growth clear on this grid, but it is still a **finite-time** estimate rather than a proof of the global bifurcation structure.
The point of the atlas is to bridge exact local stability and the visible long-time chemical oscillation, not to pretend the finite grid is the full theory.
