# Production Stewardship Gate

The production boundary is considered ready only when the service can:

1. answer the existing `/status.json` application endpoint with HTTP 200;
2. return JSON from that endpoint;
3. emit and preserve the request ID through the response;
4. pass the existing readiness checks for SQLite and writable workspace;
5. keep these checks separate from liveness so dependency failure can remove the service from traffic without implying process death.

The automated contract lives in `production_smoke.py` and `tests/test_production_smoke.py`.
