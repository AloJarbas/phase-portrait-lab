from __future__ import annotations

import sys

from .analysis import analyze_fixed_points
from .systems import CATALOG, get_system


def format_eigenvalue(value: complex) -> str:
    if abs(value.imag) < 1e-9:
        return f"{value.real:.4f}"
    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.4f} {sign} {abs(value.imag):.4f}i"


def render_system_report(slug: str) -> str:
    system = get_system(slug)
    lines = [
        f"System: {system.title} ({system.slug})",
        f"  {system.description}",
    ]
    for index, item in enumerate(analyze_fixed_points(system), start=1):
        x, y = item.point
        eig0, eig1 = item.eigenvalues
        lines.extend(
            [
                f"  Fixed point {index}: ({x:.4f}, {y:.4f})",
                f"    local type: {item.classification}",
                f"    trace={item.trace:.4f} det={item.determinant:.4f}",
                f"    eigenvalues: {format_eigenvalue(eig0)}, {format_eigenvalue(eig1)}",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args == ["--help"]:
        print("usage: python3 -m phaseportraitlab.cli <system-slug> [<system-slug> ...]")
        print("available:")
        for system in CATALOG:
            print(f"  - {system.slug}")
        return 0

    chunks: list[str] = []
    for slug in args:
        try:
            chunks.append(render_system_report(slug))
        except KeyError:
            print(f"unknown system: {slug}", file=sys.stderr)
            return 1
    print("\n\n".join(chunks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
