import unittest

import badge


class PostureColorTests(unittest.TestCase):
    def test_verdicts_map_to_colours(self):
        self.assertEqual(badge.posture_color("TRUSTWORTHY"), "#3fb950")
        self.assertEqual(badge.posture_color("INTACT"), "#d29922")
        self.assertEqual(badge.posture_color("BROKEN"), "#f85149")

    def test_unknown_is_grey(self):
        self.assertEqual(badge.posture_color("whatever"), "#8b949e")


class CviColorTests(unittest.TestCase):
    def test_at_or_above_threshold_is_green(self):
        self.assertEqual(badge.cvi_color(0.74), "#3fb950")
        self.assertEqual(badge.cvi_color(0.9), "#3fb950")
        self.assertEqual(badge.cvi_color(1.0), "#3fb950")

    def test_bands_step_down_below_threshold(self):
        self.assertEqual(badge.cvi_color(0.73), "#d29922")  # yellow near-miss
        self.assertEqual(badge.cvi_color(0.6), "#d29922")
        self.assertEqual(badge.cvi_color(0.5), "#db6d28")  # orange
        self.assertEqual(badge.cvi_color(0.4), "#db6d28")
        self.assertEqual(badge.cvi_color(0.39), "#f85149")  # red
        self.assertEqual(badge.cvi_color(0.0), "#f85149")

    def test_out_of_range_clamps(self):
        self.assertEqual(badge.cvi_color(2.0), "#3fb950")
        self.assertEqual(badge.cvi_color(-1.0), "#f85149")

    def test_non_numeric_is_grey(self):
        self.assertEqual(badge.cvi_color(None), "#8b949e")
        self.assertEqual(badge.cvi_color("x"), "#8b949e")
        self.assertEqual(badge.cvi_color(float("nan")), "#8b949e")


class AttestationMessageTests(unittest.TestCase):
    def _receipt(self, status, confidence, entry_intact=True, chain_intact=True):
        return {
            "attestation": {"status": status, "confidence": confidence},
            "entry_intact": entry_intact,
            "chain_intact": chain_intact,
        }

    def test_attested_is_green_with_confidence(self):
        msg, color = badge.attestation_message(self._receipt("attested", 0.95))
        self.assertEqual(msg, "attested 0.95")
        self.assertEqual(color, "#3fb950")

    def test_held_takes_the_threshold_aligned_colour(self):
        msg, color = badge.attestation_message(self._receipt("held", 0.61))
        self.assertEqual(msg, "held 0.61")
        self.assertEqual(color, "#d29922")  # cvi_color(0.61) — yellow, never green
        _, low = badge.attestation_message(self._receipt("held", 0.30))
        self.assertEqual(low, "#f85149")  # red

    def test_tampered_reads_red_regardless_of_confidence(self):
        msg, color = badge.attestation_message(self._receipt("attested", 0.99, entry_intact=False))
        self.assertEqual(msg, "tampered")
        self.assertEqual(color, "#f85149")
        # a broken chain voids it too
        _, c2 = badge.attestation_message(self._receipt("attested", 0.99, chain_intact=False))
        self.assertEqual(c2, "#f85149")


class SparklineTests(unittest.TestCase):
    def test_sparkline_is_svg_with_label_and_latest_value(self):
        svg = badge.sparkline([90, 94, 98], label="records")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))
        self.assertIn("records 98", svg)  # label + latest value
        self.assertIn("<polyline", svg)   # the trend line
        self.assertIn("#3fb950", svg)     # green line

    def test_sparkline_draws_a_point_per_value(self):
        svg = badge.sparkline([1, 2, 3, 4], label="records")
        points = svg.split('points="', 1)[1].split('"', 1)[0]
        self.assertEqual(len(points.split(" ")), 4)  # four coordinates

    def test_empty_series_is_a_flat_baseline_and_zero(self):
        svg = badge.sparkline([], label="records")
        self.assertIn("records 0", svg)
        self.assertIn("<polyline", svg)  # a flat baseline, never a fabricated shape

    def test_single_point_does_not_crash(self):
        svg = badge.sparkline([5], label="records")
        self.assertIn("records 5", svg)
        self.assertTrue(svg.startswith("<svg"))

    def test_normalization_keeps_points_inside_the_box(self):
        svg = badge.sparkline([10, 1000, 500], label="r")
        coords = svg.split('points="', 1)[1].split('"', 1)[0].split(" ")
        ys = [float(c.split(",")[1]) for c in coords]
        self.assertTrue(all(0 <= y <= 20 for y in ys))  # within the 20px height


class RenderTests(unittest.TestCase):
    def test_render_is_svg_with_both_cells(self):
        svg = badge.render("verification", "0.82", "#3fb950")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))
        self.assertIn("verification", svg)
        self.assertIn("0.82", svg)
        self.assertIn("#3fb950", svg)

    def test_accessible_label_present(self):
        svg = badge.render("verification", "0.82", "#3fb950")
        self.assertIn('aria-label="verification: 0.82"', svg)
        self.assertIn("<title>verification: 0.82</title>", svg)

    def test_message_text_is_escaped(self):
        svg = badge.render("l", "<script>&\"", "#000")
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)
        self.assertIn("&amp;", svg)

    def test_width_grows_with_text(self):
        short = badge.render("v", "0.8", "#000")
        long = badge.render("verification index", "0.80", "#000")
        sw = int(short.split('width="', 1)[1].split('"', 1)[0])
        lw = int(long.split('width="', 1)[1].split('"', 1)[0])
        self.assertGreater(lw, sw)

    def test_content_type_is_svg(self):
        self.assertEqual(badge.CONTENT_TYPE, "image/svg+xml")


if __name__ == "__main__":
    unittest.main()
