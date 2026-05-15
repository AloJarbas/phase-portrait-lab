from __future__ import annotations

import math
import unittest

from phaseportraitlab.analysis import analyze_fixed_points, fixed_point_residuals, trajectories, vector_field
from phaseportraitlab.brusselator_atlas import build_brusselator_parameter_atlas, estimate_brusselator_cycle_metrics
from phaseportraitlab.brusselator_sweep import brusselator_hopf_threshold, render_brusselator_hopf_report, sweep_brusselator_b_values
from phaseportraitlab.chemistry_local_global import render_chemistry_local_global_report
from phaseportraitlab.chemistry_comparison import render_chemical_oscillator_comparison_report
from phaseportraitlab.cli import render_system_report
from phaseportraitlab.integrate import rk4_step
from phaseportraitlab.selkov_atlas import build_selkov_parameter_atlas, estimate_selkov_cycle_metrics, selkov_hopf_band
from phaseportraitlab.systems import CATALOG, get_system, selkov


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
        self.assertEqual(get_system("selkov").title, "Selkov glycolysis oscillator")

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

    def test_brusselator_cycle_metrics_above_threshold(self) -> None:
        metrics = estimate_brusselator_cycle_metrics(1.0, 2.4)
        self.assertGreater(metrics.x_amplitude, 0.7)
        self.assertGreater(metrics.y_amplitude, 0.9)
        self.assertIsNotNone(metrics.period)
        self.assertAlmostEqual(metrics.period or 0.0, 6.5, delta=0.25)

    def test_brusselator_parameter_atlas_zeroes_stable_side(self) -> None:
        cells = build_brusselator_parameter_atlas([1.0], [1.6, 2.4])
        self.assertEqual(len(cells), 2)
        stable, unstable = cells
        self.assertEqual(stable.classification, "stable spiral")
        self.assertEqual(stable.x_amplitude, 0.0)
        self.assertEqual(stable.period, None)
        self.assertEqual(unstable.classification, "unstable spiral")
        self.assertGreater(unstable.x_amplitude, 0.7)
        self.assertGreater(unstable.mean_radius, 0.7)

    def test_selkov_hopf_band(self) -> None:
        lower, upper = selkov_hopf_band(0.08) or (0.0, 0.0)
        self.assertAlmostEqual(lower, 0.3464, places=3)
        self.assertAlmostEqual(upper, 0.8485, places=3)
        self.assertIsNone(selkov_hopf_band(0.13))

    def test_selkov_local_types_cross_band(self) -> None:
        stable_low = analyze_fixed_points(get_system("selkov"))[0]
        self.assertEqual(stable_low.classification, "unstable spiral")

        below = analyze_fixed_points(selkov(a=0.08, b=0.25))[0]
        inside = analyze_fixed_points(selkov(a=0.08, b=0.60))[0]
        above = analyze_fixed_points(selkov(a=0.08, b=0.95))[0]
        self.assertEqual(below.classification, "stable spiral")
        self.assertEqual(inside.classification, "unstable spiral")
        self.assertEqual(above.classification, "stable spiral")

    def test_selkov_cycle_metrics_inside_band(self) -> None:
        metrics = estimate_selkov_cycle_metrics(0.08, 0.6)
        self.assertGreater(metrics.x_amplitude, 0.55)
        self.assertGreater(metrics.y_amplitude, 0.8)
        self.assertIsNotNone(metrics.period)
        self.assertAlmostEqual(metrics.period or 0.0, 9.62, delta=0.4)

    def test_selkov_parameter_atlas_zeroes_outside_band(self) -> None:
        cells = build_selkov_parameter_atlas([0.08], [0.25, 0.6, 0.95])
        self.assertEqual(len(cells), 3)
        stable_low, unstable, stable_high = cells
        self.assertEqual(stable_low.classification, "stable spiral")
        self.assertEqual(stable_low.x_amplitude, 0.0)
        self.assertEqual(unstable.classification, "unstable spiral")
        self.assertGreater(unstable.x_amplitude, 0.55)
        self.assertIsNotNone(unstable.period)
        self.assertEqual(stable_high.classification, "stable spiral")
        self.assertEqual(stable_high.period, None)

    def test_chemical_comparison_report_mentions_finite_band(self) -> None:
        brusselator_cells = build_brusselator_parameter_atlas([1.0], [1.6, 2.4])
        selkov_cells = build_selkov_parameter_atlas([0.08], [0.25, 0.6, 0.95])
        report = render_chemical_oscillator_comparison_report(brusselator_cells, selkov_cells)
        self.assertIn("finite oscillatory band", report)
        self.assertIn("Brusselator", report)
        self.assertIn("Selkov", report)

    def test_local_global_report_mentions_jacobian_limits(self) -> None:
        brusselator_cells = build_brusselator_parameter_atlas([1.0], [1.6, 2.1, 2.4])
        selkov_cells = build_selkov_parameter_atlas([0.08], [0.25, 0.35, 0.6, 0.95])
        report = render_chemistry_local_global_report(brusselator_cells, selkov_cells)
        self.assertIn("The Jacobian does **not** answer the amplitude or period questions by itself.", report)
        self.assertIn("tiny cycle", report)
        self.assertIn("Brusselator", report)
        self.assertIn("Selkov", report)


if __name__ == "__main__":
    unittest.main()
