from __future__ import annotations

from pathlib import Path

from .analysis import trajectories, vector_field
from .systems import PlanarSystem, State


WIDTH = 1280
HEIGHT = 860
PLOT_LEFT = 110.0
PLOT_RIGHT = 860.0
PLOT_TOP = 170.0
PLOT_BOTTOM = 760.0


def map_x(x: float, x_range: tuple[float, float]) -> float:
    return PLOT_LEFT + (x - x_range[0]) / (x_range[1] - x_range[0]) * (PLOT_RIGHT - PLOT_LEFT)


def map_y(y: float, y_range: tuple[float, float]) -> float:
    return PLOT_BOTTOM - (y - y_range[0]) / (y_range[1] - y_range[0]) * (PLOT_BOTTOM - PLOT_TOP)


def text(x: float, y: float, value: str, cls: str, anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{value}</text>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, dash: str | None = None, opacity: float = 1.0) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def polyline(points: list[State], x_range: tuple[float, float], y_range: tuple[float, float], stroke: str, *, width: float = 3.0, opacity: float = 1.0) -> str:
    coords = ' '.join(
        f'{map_x(x, x_range):.1f},{map_y(y, y_range):.1f}'
        for x, y in points
    )
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-opacity="{opacity}" stroke-linejoin="round" stroke-linecap="round"/>'


def render_system(system: PlanarSystem, path: Path) -> None:
    field = vector_field(system)
    curves = trajectories(system)
    dx_segments = system.nullclines_dx(system.x_range)
    dy_segments = system.nullclines_dy(system.x_range)

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 700 20px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .tiny { font: 500 13px Helvetica, Arial, sans-serif; fill: #8aa3bc; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '    .grid { stroke: #223445; stroke-width: 1; opacity: 0.8; }',
        '    .axis { stroke: #39516a; stroke-width: 2; }',
        '  </style>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>',
        '<rect x="60" y="120" width="1160" height="690" rx="18" class="panel"/>',
        text(90, 68, system.title, 'title'),
        text(90, 98, system.description, 'subtitle'),
        text(930, 185, 'Legend', 'label'),
        text(968, 232, 'trajectories', 'small'),
        text(968, 268, 'dx/dt = 0', 'small'),
        text(968, 304, 'dy/dt = 0', 'small'),
        text(968, 340, 'fixed points', 'small'),
        circle(940, 224, 8, '#4ade80'),
        line(924, 260, 956, 260, '#f97316', 4),
        line(924, 296, 956, 296, '#60a5fa', 4),
        circle(940, 336, 7, '#f8fafc'),
        text(930, 392, 'How to read it', 'label'),
        text(930, 422, 'The arrows show the local flow.', 'small'),
        text(930, 446, 'The colored curves show where one derivative vanishes.', 'small'),
        text(930, 470, 'Trajectories reveal whether the fixed point attracts, spirals, or closes into an orbit.', 'small'),
    ]

    x0, x1 = system.x_range
    y0, y1 = system.y_range
    for tick in range(6):
        x = x0 + tick * (x1 - x0) / 5
        xp = map_x(x, system.x_range)
        svg.append(line(xp, PLOT_TOP, xp, PLOT_BOTTOM, '#223445', 1))
        svg.append(text(xp, PLOT_BOTTOM + 28, f'{x:.1f}', 'tiny', 'middle'))
    for tick in range(6):
        y = y0 + tick * (y1 - y0) / 5
        yp = map_y(y, system.y_range)
        svg.append(line(PLOT_LEFT, yp, PLOT_RIGHT, yp, '#223445', 1))
        svg.append(text(PLOT_LEFT - 18, yp + 4, f'{y:.1f}', 'tiny', 'end'))

    if x0 <= 0.0 <= x1:
        svg.append(line(map_x(0.0, system.x_range), PLOT_TOP, map_x(0.0, system.x_range), PLOT_BOTTOM, '#39516a', 2))
    if y0 <= 0.0 <= y1:
        svg.append(line(PLOT_LEFT, map_y(0.0, system.y_range), PLOT_RIGHT, map_y(0.0, system.y_range), '#39516a', 2))

    for (x, y), (dx, dy) in field:
        x1p = map_x(x, system.x_range)
        y1p = map_y(y, system.y_range)
        scale = 16.0
        x2p = map_x(x + dx * (x1 - x0) * 0.02, system.x_range)
        y2p = map_y(y + dy * (y1 - y0) * 0.02, system.y_range)
        svg.append(line(x1p, y1p, x2p, y2p, '#4b6580', 1.4, None, 0.9))

    for segment in dx_segments:
        svg.append(polyline(segment, system.x_range, system.y_range, '#f97316', width=3.2, opacity=0.9))
    for segment in dy_segments:
        svg.append(polyline(segment, system.x_range, system.y_range, '#60a5fa', width=3.2, opacity=0.9))
    for curve in curves:
        svg.append(polyline(curve, system.x_range, system.y_range, '#4ade80', width=2.6, opacity=0.72))
    for x, y in system.fixed_points:
        svg.append(circle(map_x(x, system.x_range), map_y(y, system.y_range), 6.0, '#f8fafc'))

    svg.append(text(PLOT_LEFT, 788, 'Generated from a standard-library Python gallery: vector field + nullclines + trajectories.', 'small'))
    svg.append('</svg>')

    path.write_text('\n'.join(svg) + '\n')
