"""Tests for dashboard.py — Dashboard functionality.

Covers:
  - add() default status 'active'
  - add() custom status override
  - add() multiple items and summary()
  - summary() on empty dashboard
  - summary() items returns copy of internal list
"""
import unittest

from dashboard import Dashboard


class DashboardTests(unittest.TestCase):

    def test_add_default_status(self):
        dashboard = Dashboard()
        item = dashboard.add("Plan charter", "plan")
        self.assertEqual(item["title"], "Plan charter")
        self.assertEqual(item["kind"], "plan")
        self.assertEqual(item["status"], "active")

    def test_add_custom_status(self):
        dashboard = Dashboard()
        item = dashboard.add("Archived task", "task", status="archived")
        self.assertEqual(item["status"], "archived")

    def test_summary_multiple_items(self):
        dashboard = Dashboard()
        dashboard.add("Item 1", "kind1")
        dashboard.add("Item 2", "kind2")
        summary = dashboard.summary()
        self.assertEqual(summary["count"], 2)
        self.assertEqual(len(summary["items"]), 2)
        self.assertEqual(summary["items"][0]["title"], "Item 1")
        self.assertEqual(summary["items"][1]["kind"], "kind2")

    def test_empty_dashboard_summary(self):
        dashboard = Dashboard()
        summary = dashboard.summary()
        self.assertEqual(summary["count"], 0)
        self.assertEqual(summary["items"], [])

    def test_summary_items_returns_copy(self):
        dashboard = Dashboard()
        dashboard.add("Item 1", "kind1")
        summary = dashboard.summary()
        summary["items"].append({"title": "fake", "kind": "fake", "status": "fake"})
        self.assertEqual(dashboard.summary()["count"], 1)


if __name__ == "__main__":
    unittest.main()

