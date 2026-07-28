"""Tests for openapi.py — self-describing API spec generated from live routes.

Covers:
  - Spec skeleton: openapi version, info title/version
  - Known path /cvi has GET with summary and operationId
  - Parameterized path types its argument (integer att_id)
  - HEAD and OPTIONS are excluded from all paths
  - static route is absent
  - Core endpoint paths are all documented
  - All 8 Oceanic VaaS endpoints are in the spec
  - VaaS endpoints have correct HTTP methods
  - info description field is present
  - paths is a non-empty dict
  - operationId follows method_endpoint format
"""
import unittest

import openapi
from app import app


class OpenApiGenerateTests(unittest.TestCase):
    def setUp(self):
        self.spec = openapi.generate(
            app.url_map, app.view_functions, title="Test API", version="9.9"
        )

    def test_valid_skeleton(self):
        self.assertEqual(self.spec["openapi"], "3.0.3")
        self.assertEqual(self.spec["info"]["title"], "Test API")
        self.assertEqual(self.spec["info"]["version"], "9.9")
        self.assertTrue(self.spec["paths"])

    def test_known_path_has_get_with_summary(self):
        cvi = self.spec["paths"]["/cvi"]
        self.assertIn("get", cvi)
        self.assertTrue(cvi["get"]["summary"])
        self.assertEqual(cvi["get"]["operationId"], "get_composite_verification_index")

    def test_parameterized_path_types_its_argument(self):
        op = self.spec["paths"]["/attestations/{att_id}/review"]["post"]
        params = op["parameters"]
        att = next(p for p in params if p["name"] == "att_id")
        self.assertEqual(att["in"], "path")
        self.assertTrue(att["required"])
        self.assertEqual(att["schema"]["type"], "integer")

    def test_head_and_options_are_excluded(self):
        for path, item in self.spec["paths"].items():
            self.assertNotIn("head", item)
            self.assertNotIn("options", item)

    def test_static_route_is_absent(self):
        self.assertFalse(any("static" in p for p in self.spec["paths"]))

    def test_every_round_endpoint_is_documented(self):
        # the generated surface reflects endpoints added across many rounds
        for path in ("/metrics", "/cvi/history", "/rules/evaluate", "/attestations/export", "/anchor"):
            self.assertIn(path, self.spec["paths"])

    def test_all_vaas_endpoints_are_in_spec(self):
        """All 8 Oceanic VaaS endpoints added in the /goal session must be documented."""
        vaas_paths = [
            "/oceanic/contracts",
            "/oceanic/verify",
            "/oceanic/attest",
            "/oceanic/lifecycle/run",
            "/oceanic/lifecycle/events",
            "/oceanic/lifecycle/chain/verify",
            "/oceanic/drift/stats",
            "/oceanic/perspectives",
        ]
        for path in vaas_paths:
            self.assertIn(path, self.spec["paths"], f"VaaS path missing from spec: {path}")

    def test_vaas_post_endpoints_have_post_method(self):
        for path in ("/oceanic/contracts", "/oceanic/verify", "/oceanic/attest",
                     "/oceanic/lifecycle/run", "/oceanic/perspectives"):
            item = self.spec["paths"][path]
            self.assertIn("post", item, f"Expected POST on {path}")

    def test_vaas_get_endpoints_have_get_method(self):
        for path in ("/oceanic/lifecycle/events", "/oceanic/lifecycle/chain/verify",
                     "/oceanic/drift/stats"):
            item = self.spec["paths"][path]
            self.assertIn("get", item, f"Expected GET on {path}")

    def test_info_description_field_is_present(self):
        self.assertIn("description", self.spec["info"])

    def test_paths_is_nonempty_dict(self):
        self.assertIsInstance(self.spec["paths"], dict)
        self.assertGreater(len(self.spec["paths"]), 0)

    def test_operationid_follows_method_endpoint_format(self):
        # operationId should be "{method}_{endpoint_name}"
        cvi_get_op = self.spec["paths"]["/cvi"]["get"]
        self.assertTrue(cvi_get_op["operationId"].startswith("get_"))

    def test_responses_key_present_on_every_operation(self):
        for path, item in self.spec["paths"].items():
            for method, operation in item.items():
                self.assertIn("responses", operation, f"Missing responses on {method.upper()} {path}")


if __name__ == "__main__":
    unittest.main()

