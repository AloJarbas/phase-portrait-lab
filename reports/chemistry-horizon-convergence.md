# Chemistry horizon convergence sidecar

This pass asks one bounded question: **if the Jacobian already told us where oscillation begins, how much does a longer integration horizon still change the measured newborn cycle?**

The answer in both chemistry models is the same in spirit:

- near threshold, a short settle window makes the x-amplitude look too large
- the period is much less sensitive over the same range
- farther from threshold, the two horizons nearly agree

## Brusselator anchor

At `A = 1.00`, the exact Hopf edge is `B = 1 + A^2 = 2.00`.
At the smallest sampled offset `ΔB = 0.01`, the short horizon gives `x amplitude = 0.235` while the long horizon gives `0.126`. The period only moves from `6.300` to `6.287`.
By `ΔB = 0.28`, the amplitude gap has collapsed to `0.000`.

## Selkov anchor

At `a = 0.080`, the lower Hopf edge sits at `b ≈ 0.346`.
At the smallest sampled offset `Δb = 0.003`, the short horizon gives `x amplitude = 0.112` while the long horizon gives `0.069`. The period only moves from `14.080` to `14.020`.
By `Δb = 0.160`, the amplitude gap has collapsed to `0.000`.

## What this changes in the repo story

The local-versus-global note already said that the Jacobian does not give amplitude or period by itself.
This sidecar tightens that claim: even once we do integrate the orbit, a finite scan horizon can still make the brand-new cycle look larger than it really is, while the period is already almost settled.

Across this card, the largest period shift between the short and long horizons is only `0.060` time units.

## Open next

- `assets/chemistry-horizon-convergence.svg`
- `assets/chemistry-horizon-convergence.png`
- `assets/chemistry-horizon-convergence.csv`
- `reports/chemistry-horizon-convergence.md`
- `notebooks/chemistry_horizon_convergence.ipynb`
