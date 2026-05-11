from __future__ import annotations

import math
from typing import Iterable

from .integrate import integrate_path
from .systems import PlanarSystem, State


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
