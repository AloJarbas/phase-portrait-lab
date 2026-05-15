# Brusselator Hopf sweep

This report tracks the Brusselator fixed point while `A = 1.0` stays fixed and `B` moves through the Hopf threshold `B = 1 + A^2 = 2.00`.

At the fixed point `(x*, y*) = (A, B / A)`, the Jacobian is

```text
[ B - 1    A^2 ]
[  -B     -A^2 ]
```

so the trace is `B - 1 - A^2 = B - 2.00` and the determinant is `A^2 = 1.00`.

## Sampled sweep

| B | fixed point | trace | Re(λ) | Im(λ) magnitude | local type |
| --- | --- | ---: | ---: | ---: | --- |
| 1.20 | (1.00, 1.20) | -0.800 | -0.400 | 0.917 | stable spiral |
| 1.30 | (1.00, 1.30) | -0.700 | -0.350 | 0.937 | stable spiral |
| 1.40 | (1.00, 1.40) | -0.600 | -0.300 | 0.954 | stable spiral |
| 1.50 | (1.00, 1.50) | -0.500 | -0.250 | 0.968 | stable spiral |
| 1.60 | (1.00, 1.60) | -0.400 | -0.200 | 0.980 | stable spiral |
| 1.70 | (1.00, 1.70) | -0.300 | -0.150 | 0.989 | stable spiral |
| 1.80 | (1.00, 1.80) | -0.200 | -0.100 | 0.995 | stable spiral |
| 1.90 | (1.00, 1.90) | -0.100 | -0.050 | 0.999 | stable spiral |
| 2.00 | (1.00, 2.00) | 0.000 | 0.000 | 1.000 | center-like |
| 2.10 | (1.00, 2.10) | 0.100 | 0.050 | 0.999 | unstable spiral |
| 2.20 | (1.00, 2.20) | 0.200 | 0.100 | 0.995 | unstable spiral |
| 2.30 | (1.00, 2.30) | 0.300 | 0.150 | 0.989 | unstable spiral |
| 2.40 | (1.00, 2.40) | 0.400 | 0.200 | 0.980 | unstable spiral |
| 2.50 | (1.00, 2.50) | 0.500 | 0.250 | 0.968 | unstable spiral |
| 2.60 | (1.00, 2.60) | 0.600 | 0.300 | 0.954 | unstable spiral |
| 2.70 | (1.00, 2.70) | 0.700 | 0.350 | 0.937 | unstable spiral |
| 2.80 | (1.00, 2.80) | 0.800 | 0.400 | 0.917 | unstable spiral |

## Reading the sweep

- for `B < 2.00`, the real part is negative, so perturbations spiral inward
- at `B = 2.00`, the trace hits zero and the linearization lands on the Hopf boundary
- for `B > 2.00`, the real part turns positive, so the fixed point repels while oscillatory structure remains
- the generated SVG in `assets/brusselator-hopf-sweep.svg` puts the trace, eigenvalue drift, and local reading on one card
