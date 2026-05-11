from __future__ import annotations

import math
import unittest

from phaseportraitlab.analysis import fixed_point_residuals, trajectories, vector_field
from phaseportraitlab.integrate import rk4_step
from phaseportraitlab.systems import CATALOG, get_system


class PhasePortraitTests(unittest.TestCase):
    def test_known_fixed_points_have_small_residuals(self) -> None:
        for system in CATALOG:
            for residual in fixed_point_residuals(system):
                self.assertLess(residual, 1e-9, msg=system.slug)

    def test_rk4_matches_small_step_harmonic_motion(self) -> None:
        def harmonic(x: float, y: float) -> tuple[float, float]:
            return (y, -x)

        x, y = rk4_step(harmonic, (1.0, 0.0), 0.01)
        self.assertAlmostEqual(x, math.cos(0.01), places=6)
        self.assertAlmostEqual(y, -math.sin(0.01), places=6)

    def test_gallery_primitives_are_nonempty(self) -> None:
        for system in CATALOG:
            self.assertTrue(vector_field(system))
            self.assertTrue(trajectories(system))

    def test_lookup_by_slug(self) -> None:
        self.assertEqual(get_system("brusselator").title, "Brusselator")


if __name__ == "__main__":
    unittest.main()
