from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

State = tuple[float, float]
Derivative = Callable[[float, float], State]
NullclineBuilder = Callable[[tuple[float, float]], list[list[State]]]


@dataclass(frozen=True)
class PlanarSystem:
    slug: str
    title: str
    description: str
    x_range: tuple[float, float]
    y_range: tuple[float, float]
    derivatives: Derivative
    fixed_points: tuple[State, ...]
    trajectories: tuple[State, ...]
    nullclines_dx: NullclineBuilder
    nullclines_dy: NullclineBuilder


def sample_curve(func: Callable[[float], float | None], x_range: tuple[float, float], *, points: int = 300, y_limit: float = 20.0) -> list[list[State]]:
    x0, x1 = x_range
    step = (x1 - x0) / (points - 1)
    segments: list[list[State]] = []
    current: list[State] = []
    for index in range(points):
        x = x0 + index * step
        y = func(x)
        if y is None or not (-y_limit <= y <= y_limit):
            if len(current) > 1:
                segments.append(current)
            current = []
            continue
        current.append((x, y))
    if len(current) > 1:
        segments.append(current)
    return segments


def vandepol() -> PlanarSystem:
    mu = 1.5

    def derivatives(x: float, y: float) -> State:
        return (y, mu * (1.0 - x * x) * y - x)

    def dx_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        x0, x1 = x_range
        return [[(x0, 0.0), (x1, 0.0)]]

    def dy_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        def curve(x: float) -> float | None:
            denom = mu * (1.0 - x * x)
            if abs(denom) < 1e-6:
                return None
            return x / denom
        return sample_curve(curve, x_range)

    return PlanarSystem(
        slug="vanderpol",
        title="Van der Pol oscillator",
        description="A self-excited oscillator that pushes outward near the origin and damps harder at larger amplitude.",
        x_range=(-3.0, 3.0),
        y_range=(-4.0, 4.0),
        derivatives=derivatives,
        fixed_points=((0.0, 0.0),),
        trajectories=((-2.2, 0.2), (-0.5, 2.2), (1.8, -2.4), (2.6, 1.4)),
        nullclines_dx=dx_nullclines,
        nullclines_dy=dy_nullclines,
    )


def lotka_volterra() -> PlanarSystem:
    alpha, beta, gamma, delta = 1.5, 1.0, 1.0, 1.0

    def derivatives(x: float, y: float) -> State:
        return (alpha * x - beta * x * y, delta * x * y - gamma * y)

    def dx_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        x0, x1 = x_range
        return [[(x0, alpha / beta), (x1, alpha / beta)], [(0.0, 0.0), (0.0, 3.4)]]

    def dy_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        x0, x1 = x_range
        return [[(x0, 0.0), (x1, 0.0)], [(gamma / delta, 0.0), (gamma / delta, 3.4)]]

    return PlanarSystem(
        slug="lotka-volterra",
        title="Lotka-Volterra predator-prey",
        description="Closed orbits around a coexistence point, with prey feeding predator growth and predators draining prey.",
        x_range=(0.0, 3.4),
        y_range=(0.0, 3.4),
        derivatives=derivatives,
        fixed_points=((0.0, 0.0), (gamma / delta, alpha / beta)),
        trajectories=((0.4, 0.5), (1.7, 0.6), (2.7, 1.4), (0.8, 2.4)),
        nullclines_dx=dx_nullclines,
        nullclines_dy=dy_nullclines,
    )


def brusselator() -> PlanarSystem:
    a, b = 1.0, 2.4

    def derivatives(x: float, y: float) -> State:
        return (a + x * x * y - (b + 1.0) * x, b * x - x * x * y)

    def dx_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        def curve(x: float) -> float | None:
            if abs(x) < 1e-6:
                return None
            return ((b + 1.0) * x - a) / (x * x)
        return sample_curve(curve, x_range)

    def dy_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        def curve(x: float) -> float | None:
            if abs(x) < 1e-6:
                return None
            return b / x
        return sample_curve(curve, x_range)

    return PlanarSystem(
        slug="brusselator",
        title="Brusselator",
        description="A textbook autocatalytic oscillator model with a fixed point that loses calm and grows a limit cycle.",
        x_range=(0.2, 3.2),
        y_range=(0.0, 4.5),
        derivatives=derivatives,
        fixed_points=((a, b / a),),
        trajectories=((0.5, 0.4), (1.0, 0.3), (2.2, 1.4), (2.8, 3.2)),
        nullclines_dx=dx_nullclines,
        nullclines_dy=dy_nullclines,
    )


def linear_saddle() -> PlanarSystem:
    def derivatives(x: float, y: float) -> State:
        return (x, -y)

    def dx_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        _x0, _x1 = x_range
        return [[(0.0, -2.4), (0.0, 2.4)]]

    def dy_nullclines(x_range: tuple[float, float]) -> list[list[State]]:
        x0, x1 = x_range
        return [[(x0, 0.0), (x1, 0.0)]]

    return PlanarSystem(
        slug="linear-saddle",
        title="Linear saddle",
        description="The cleanest local-stability example in the repo: one axis attracts, the other repels.",
        x_range=(-2.4, 2.4),
        y_range=(-2.4, 2.4),
        derivatives=derivatives,
        fixed_points=((0.0, 0.0),),
        trajectories=((-1.9, 1.4), (-1.6, 0.4), (0.4, 1.8), (1.5, -1.2), (0.0, 1.8), (1.8, 0.0)),
        nullclines_dx=dx_nullclines,
        nullclines_dy=dy_nullclines,
    )


CATALOG: tuple[PlanarSystem, ...] = (linear_saddle(), vandepol(), lotka_volterra(), brusselator())


def get_system(slug: str) -> PlanarSystem:
    for system in CATALOG:
        if system.slug == slug:
            return system
    raise KeyError(slug)
