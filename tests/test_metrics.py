"""Tests for metrics.py — Prometheus text exposition format renderer.

Covers:
  - render() emits # HELP, # TYPE, and sample line
  - Booleans render as 1 or 0
  - type defaults to 'gauge', can be overridden to 'counter'
  - Integers render without decimals
  - Empty metrics list produces just a trailing newline
  - Float value uses repr for precision
  - Multiple metrics rendered in order
  - CONTENT_TYPE constant is correct Prometheus text format
  - Output always ends with newline
  - Negative values render correctly
  - Zero integer renders as '0'
"""
import unittest

import metrics


class MetricsRenderTests(unittest.TestCase):

    def test_render_emits_help_type_and_sample(self):
        text = metrics.render(
            [{"name": "oceanicos_cvi", "help": "the index", "value": 0.8}]
        )
        self.assertIn("# HELP oceanicos_cvi the index", text)
        self.assertIn("# TYPE oceanicos_cvi gauge", text)
        self.assertIn("oceanicos_cvi 0.8", text)
        self.assertTrue(text.endswith("\n"))

    def test_booleans_render_as_one_or_zero(self):
        text = metrics.render(
            [
                {"name": "up", "help": "h", "value": True},
                {"name": "down", "help": "h", "value": False},
            ]
        )
        self.assertIn("\nup 1", text)
        self.assertIn("\ndown 0", text)

    def test_type_defaults_to_gauge_and_can_be_overridden(self):
        text = metrics.render(
            [{"name": "n", "help": "h", "value": 1, "type": "counter"}]
        )
        self.assertIn("# TYPE n counter", text)

    def test_integers_render_without_decimals(self):
        text = metrics.render([{"name": "n", "help": "h", "value": 42}])
        self.assertIn("n 42\n", text)

    def test_empty_metrics_list_produces_trailing_newline_only(self):
        text = metrics.render([])
        self.assertEqual(text, "\n")

    def test_float_value_uses_repr_precision(self):
        text = metrics.render([{"name": "ratio", "help": "h", "value": 0.1 + 0.2}])
        # repr(0.1 + 0.2) = '0.30000000000000004'
        self.assertIn("ratio " + repr(0.1 + 0.2), text)

    def test_multiple_metrics_in_order(self):
        text = metrics.render([
            {"name": "first", "help": "f", "value": 1},
            {"name": "second", "help": "s", "value": 2},
            {"name": "third", "help": "t", "value": 3},
        ])
        pos_first = text.index("first")
        pos_second = text.index("second")
        pos_third = text.index("third")
        self.assertLess(pos_first, pos_second)
        self.assertLess(pos_second, pos_third)

    def test_content_type_constant_is_prometheus_format(self):
        self.assertIn("text/plain", metrics.CONTENT_TYPE)
        self.assertIn("0.0.4", metrics.CONTENT_TYPE)

    def test_output_always_ends_with_newline(self):
        for value in (0, 1, True, False, 0.5, -1):
            text = metrics.render([{"name": "m", "help": "h", "value": value}])
            self.assertTrue(text.endswith("\n"), f"No trailing newline for value={value!r}")

    def test_negative_value_renders_correctly(self):
        text = metrics.render([{"name": "neg", "help": "h", "value": -42}])
        self.assertIn("neg -42\n", text)

    def test_zero_integer_renders_as_zero(self):
        text = metrics.render([{"name": "z", "help": "h", "value": 0}])
        self.assertIn("z 0\n", text)


if __name__ == "__main__":
    unittest.main()

