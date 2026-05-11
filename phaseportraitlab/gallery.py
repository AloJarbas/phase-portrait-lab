from __future__ import annotations

from pathlib import Path

from .svg import render_system
from .systems import CATALOG


def build_gallery(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for system in CATALOG:
        path = output_dir / f"{system.slug}-phase-portrait.svg"
        render_system(system, path)
        paths.append(path)
    return paths
