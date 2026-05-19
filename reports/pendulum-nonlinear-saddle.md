# Nonlinear saddle sidecar: the pendulum separatrix bends

The linear saddle in the main gallery is still worth keeping. But it teaches only the first local sentence: one direction attracts and one direction repels.

The simple pendulum adds the next sentence. The upright equilibrium is also a saddle, yet its invariant set is not a pair of straight lines across the whole plane. The barrier is an exact energy contour.

## Exact object

For the undamped pendulum

- `θ' = ω`
- `ω' = -sin θ`

the conserved energy is

- `H(θ, ω) = 1 - cos θ + ω² / 2`

The upright equilibrium sits at `θ = π`, `ω = 0` with energy `H = 2`. So the separatrix is the exact level set `H = 2`.

Shift the angle with `φ = θ - π`. On that local coordinate, the separatrix branches become

- `ω = ± 2 sin(φ / 2)`

and the linearized saddle only sees the tangent lines

- `ω = ± φ`

## What the sidecar measures

The CSV sidecar tracks the positive branch for `0 ≤ φ ≤ π` and compares the exact `2 sin(φ/2)` branch to the linear `φ` tangent.

Selected checkpoints:

- `φ = 0.209` → exact `ω = 0.209`, linear `ω = 0.209`, absolute error `= 0.000`
- `φ = 0.559` → exact `ω = 0.551`, linear `ω = 0.559`, absolute error `= 0.007`
- `φ = 1.257` → exact `ω = 1.176`, linear `ω = 1.257`, absolute error `= 0.081`
- `φ = 3.142` → exact `ω = 2.000`, linear `ω = 3.142`, absolute error `= 1.142`

## Read of the picture

- the full portrait shows closed oscillations below the barrier and the highlighted separatrix as the exact divide between trapped motion and rotation
- the local zoom shows why the Jacobian is still useful: the exact branches leave the saddle with the same tangent lines the linear model predicts
- the error panel shows why the local model should not be promoted into a global picture: the branch keeps bending while the linear line keeps climbing

## Why this belongs in the repo

The gallery already had a perfect straight saddle. This pass adds the missing counterweight: a system where the local saddle classification is right, but the global manifolds are curved enough that the local picture is visibly incomplete.

## Caveat

This sidecar uses the undamped pendulum because the energy integral is exact and readable. That makes it a geometry note, not a broad claim about every nonlinear saddle.

Open `assets/pendulum-nonlinear-saddle.svg`, `assets/pendulum-nonlinear-saddle.png`, `assets/pendulum-nonlinear-saddle.csv`, and `notebooks/pendulum_nonlinear_saddle.ipynb` next.
