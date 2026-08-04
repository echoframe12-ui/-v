from flask import Flask

from omega_edge_http_registration import register_omega_edge


def test_registration_is_explicit_and_idempotent():
    app = Flask(__name__)
    assert register_omega_edge(app) is app
    register_omega_edge(app)
    assert "/omega/edge/verify" in {rule.rule for rule in app.url_map.iter_rules()}
