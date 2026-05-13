from __future__ import annotations

from dataclasses import dataclass
import math

from .integrate import integrate_path
from .systems import PlanarSystem, State


@dataclass(frozen=True)
class FixedPointAnalysis:
    point: State
    jacobian: tuple[tuple[float, float], tuple[float, float]]
    trace: float
    determinant: float
    discriminant: float
    eigenvalues: tuple[complex, complex]
    classification: str


def vector_field(system: PlanarSystem, *, nx: int = 17, ny: int = 13) -> list[tuple[State, State]]:
    x0, x1 = system.x_range
    y0, y1 = system.y_range
    field: list[tuple[State, State]] = []
    for ix in range(nx):
        x = x0 + ix * (x1 - x0) / (nx - 1)
        for iy in range(ny):
            y = y0 + iy * (y1 - y0) / (ny - 1)
            dx, dy = system.derivatives(x, y)
            mag = math.hypot(dx, dy)
            if mag < 1e-12:
                continue
            field.append(((x, y), (dx / mag, dy / mag)))
    return field


def trajectories(system: PlanarSystem, *, dt: float = 0.025, steps: int = 1000) -> list[list[State]]:
    bounds = (system.x_range, system.y_range)
    curves: list[list[State]] = []
    for start in system.trajectories:
        forward = integrate_path(system.derivatives, start, dt=dt, steps=steps, bounds=bounds)
        backward = integrate_path(system.derivatives, start, dt=-dt, steps=steps // 2, bounds=bounds)
        full = list(reversed(backward[1:])) + forward
        curves.append(full)
    return curves


def fixed_point_residuals(system: PlanarSystem) -> list[float]:
    residuals = []
    for x, y in system.fixed_points:
        dx, dy = system.derivatives(x, y)
        residuals.append(abs(dx) + abs(dy))
    return residuals


def jacobian(system: PlanarSystem, point: State, *, step: float = 1e-5) -> tuple[tuple[float, float], tuple[float, float]]:
    x, y = point
    dx_x_plus, dy_x_plus = system.derivatives(x + step, y)
    dx_x_minus, dy_x_minus = system.derivatives(x - step, y)
    dx_y_plus, dy_y_plus = system.derivatives(x, y + step)
    dx_y_minus, dy_y_minus = system.derivatives(x, y - step)

    dfdx = (dx_x_plus - dx_x_minus) / (2.0 * step)
    dfdy = (dx_y_plus - dx_y_minus) / (2.0 * step)
    dgdx = (dy_x_plus - dy_x_minus) / (2.0 * step)
    dgdy = (dy_y_plus - dy_y_minus) / (2.0 * step)
    return ((dfdx, dfdy), (dgdx, dgdy))


def classify_fixed_point(trace: float, determinant: float, discriminant: float, *, tol: float = 1e-9) -> str:
    if determinant < -tol:
        return "saddle"
    if abs(determinant) <= tol and abs(trace) <= tol:
        return "degenerate"
    if discriminant > tol:
        if trace < -tol:
            return "stable node"
        if trace > tol:
            return "unstable node"
    elif discriminant < -tol:
        if abs(trace) <= tol:
            return "center-like"
        if trace < -tol:
            return "stable spiral"
        if trace > tol:
            return "unstable spiral"
    else:
        if trace < -tol:
            return "repeated-root sink"
        if trace > tol:
            return "repeated-root source"
    return "degenerate"


def eigenvalues_from_trace_det(trace: float, determinant: float) -> tuple[complex, complex]:
    discriminant = complex(trace * trace - 4.0 * determinant, 0.0)
    root = discriminant ** 0.5
    return ((trace + root) / 2.0, (trace - root) / 2.0)


def analyze_fixed_points(system: PlanarSystem) -> list[FixedPointAnalysis]:
    analyses: list[FixedPointAnalysis] = []
    for point in system.fixed_points:
        (a, b), (c, d) = jacobian(system, point)
        trace = a + d
        determinant = a * d - b * c
        discriminant = trace * trace - 4.0 * determinant
        analyses.append(
            FixedPointAnalysis(
                point=point,
                jacobian=((a, b), (c, d)),
                trace=trace,
                determinant=determinant,
                discriminant=discriminant,
                eigenvalues=eigenvalues_from_trace_det(trace, determinant),
                classification=classify_fixed_point(trace, determinant, discriminant),
            )
        )
    return analyses
