from __future__ import annotations

"""Optional registration helper for the Ω∞v Edge HTTP blueprint.

The existing Flask application remains untouched until this helper is explicitly
called, preventing a transport concern from silently changing application startup.
"""

from flask import Flask

from omega_edge_http import edge_blueprint


def register_omega_edge(app: Flask) -> Flask:
    """Register the Ω∞v Edge blueprint exactly once."""
    if "omega_edge" not in app.blueprints:
        app.register_blueprint(edge_blueprint)
    return app
