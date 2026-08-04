# Production gate index

- Executable smoke: `production_smoke.py`
- Stewardship contract: `STEWARDSHIP_PRODUCTION_GATE.md`
- Runtime boundary: existing Flask `/status.json` plus `readiness.probe()`.
