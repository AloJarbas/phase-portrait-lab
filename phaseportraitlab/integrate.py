from __future__ import annotations

from typing import Callable

State = tuple[float, float]
Derivative = Callable[[float, float], State]


def rk4_step(derivatives: Derivative, state: State, dt: float) -> State:
    x, y = state
    k1x, k1y = derivatives(x, y)
    k2x, k2y = derivatives(x + 0.5 * dt * k1x, y + 0.5 * dt * k1y)
    k3x, k3y = derivatives(x + 0.5 * dt * k2x, y + 0.5 * dt * k2y)
    k4x, k4y = derivatives(x + dt * k3x, y + dt * k3y)
    next_x = x + (dt / 6.0) * (k1x + 2.0 * k2x + 2.0 * k3x + k4x)
    next_y = y + (dt / 6.0) * (k1y + 2.0 * k2y + 2.0 * k3y + k4y)
    return (next_x, next_y)


def integrate_path(derivatives: Derivative, start: State, *, dt: float, steps: int, bounds: tuple[tuple[float, float], tuple[float, float]]) -> list[State]:
    x_bounds, y_bounds = bounds
    points = [start]
    state = start
    for _ in range(steps):
        state = rk4_step(derivatives, state, dt)
        x, y = state
        if not (x_bounds[0] - 0.4 <= x <= x_bounds[1] + 0.4 and y_bounds[0] - 0.4 <= y <= y_bounds[1] + 0.4):
            break
        points.append(state)
    return points
