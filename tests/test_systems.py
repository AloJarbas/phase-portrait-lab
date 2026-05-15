from __future__ import annotations

import math
import unittest

from phaseportraitlab.analysis import analyze_fixed_points, fixed_point_residuals, trajectories, vector_field
from phaseportraitlab.brusselator_sweep import brusselator_hopf_threshold, render_brusselator_hopf_report, sweep_brusselator_b_values
from phaseportraitlab.cli import render_system_report
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

    def test_linear_saddle_is_classified_as_saddle(self) -> None:
        analysis = analyze_fixed_points(get_system("linear-saddle"))
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0].classification, "saddle")
        eigs = sorted((eig.real for eig in analysis[0].eigenvalues))
        self.assertAlmostEqual(eigs[0], -1.0, places=4)
        self.assertAlmostEqual(eigs[1], 1.0, places=4)

    def test_lotka_volterra_coexistence_point_is_center_like(self) -> None:
        analysis = analyze_fixed_points(get_system("lotka-volterra"))
        self.assertEqual(analysis[1].classification, "center-like")

    def test_cli_report_mentions_local_type(self) -> None:
        report = render_system_report("linear-saddle")
        self.assertIn("local type: saddle", report)
        self.assertIn("eigenvalues:", report)

    def test_brusselator_hopf_threshold_and_local_types(self) -> None:
        self.assertAlmostEqual(brusselator_hopf_threshold(1.0), 2.0)
        rows = sweep_brusselator_b_values([1.6, 2.0, 2.4])
        self.assertEqual([row.classification for row in rows], ["stable spiral", "center-like", "unstable spiral"])
        self.assertLess(rows[0].decay_rate, 0.0)
        self.assertAlmostEqual(rows[1].trace, 0.0, places=4)
        self.assertGreater(rows[2].decay_rate, 0.0)

    def test_brusselator_report_mentions_threshold(self) -> None:
        report = render_brusselator_hopf_report(sweep_brusselator_b_values([1.6, 2.0, 2.4]))
        self.assertIn("Brusselator Hopf sweep", report)
        self.assertIn("B = 1 + A^2 = 2.00", report)
        self.assertIn("stable spiral", report)


if __name__ == "__main__":
    unittest.main()
