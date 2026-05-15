# Chemical oscillator comparison

This short note compares the two chemistry-facing oscillators now living in `phase-portrait-lab`.
Both models show a Hopf-style bridge from local linearization to a visible long-time cycle, but the parameter geometry is different enough to be worth seeing side by side.

## 1. Local bifurcation geometry

### Brusselator

- equations: `dx/dt = A + x^2 y - (B + 1)x`, `dy/dt = Bx - x^2 y`
- exact local boundary: `B = 1 + A^2`, so at `A = 1.00` the threshold is `B = 2.00`
- local reading: one smooth curve splits parameter space into a stable side and a one-sided oscillatory side

### Selkov

- equations: `dx/dt = -x + a y + x^2 y`, `dy/dt = b - a y - x^2 y`
- exact local boundaries at `a = 0.05`: `b ∈ (0.250, 0.915)` is the unstable window
- exact local boundaries at `a = 0.08`: `b ∈ (0.346, 0.849)` is the unstable window
- local reading: two Hopf curves create a finite oscillatory band, so the fixed point is stable below the band and stable again above it

## 2. Global cycle reading on the sampled grids

- sampled Brusselator oscillatory cells with measured periods: `149`
- sampled Selkov oscillatory cells with measured periods: `117`
- Brusselator anchor (`A = 0.95`, `B = 2.39`): `x` amplitude `0.97`, period `6.91`
- Selkov anchor (`a = 0.080`, `b = 0.60`): `x` amplitude `0.64`, period `9.62`

## 3. Why the contrast matters

- the Brusselator atlas is a clean one-threshold story: move far enough above one exact curve and the self-sustained cycle keeps growing
- the Selkov atlas is a finite-band story: oscillation turns on after the lower Hopf edge, but it also turns off again after the upper edge
- together they make the chemistry lane in this repo more honest: Hopf language is shared, but the global parameter geography is model-specific

## Files to open

- `assets/brusselator-parameter-atlas.svg`
- `assets/selkov-parameter-atlas.svg`
- `reports/brusselator-parameter-atlas.md`
- `reports/selkov-parameter-atlas.md`
