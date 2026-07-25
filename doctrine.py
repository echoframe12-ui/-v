"""The Ω∞v Doctrine, as a code-backed map — each layer points at what implements it.

The Doctrine (DOCTRINE.md) is the system's compressed self-definition. This module
holds it as structured data: every layer names the endpoints, modules, decision
records, and documents that make it real, plus an honest `shipped` flag. The
platform's own creed is *attest, don't assert* — so the Doctrine is held to the
same discipline as docs/POSITIONING.md: a claim of "shipped" that does not point
at resolvable code is a bug the test suite catches. Two layers are deliberately
`shipped: False` — the physical binary and hardware key are out of scope for a
repository, and the Doctrine says so rather than pretending.
"""
from __future__ import annotations

from typing import Any

AXIOMS = [
    "Certainty is a bug.",
    "Dissent is data.",
    "Friction is fertility.",
    "Verification is the product.",
    "Continuous Becoming is the system state.",
]

CHECKSUM = "Gap → Friction → Verification → VaaS → Ω∞v → Observer → Continuous Becoming"

# The umbrella identity for the whole ecosystem (the Ω∞ Oceanic master handoff).
UMBRELLA = "Ω∞ Oceanic"

# The master loop — the compressed lifecycle of the whole ecosystem, a superset of
# the CHECKSUM_LINE that adds the ecosystem's outer arc (observation, accountability,
# consequence, learning) around the same verification core.
MASTER_LOOP = (
    "Source → Current → Creation → Form → Intelligence → Observation → Divergence "
    "→ Dissent → Verification → Attestation → Accountability → Action → Consequence "
    "→ Learning → Drift → Recompilation → ∞"
)

MASTER_AXIOM = (
    "One Current. Infinite Forms. Many Minds. One Verification Fabric. Continuous Becoming."
)

MASTER_DEFINITION = (
    "Ω∞ Oceanic is a living, local-first intelligence ecosystem in which the Source — "
    "the Current — moves through infinite biological and computational forms, allowing "
    "many intelligences to observe reality, surface dissent, verify evidence, preserve "
    "provenance, act proactively under human accountability, learn from consequences, and "
    "continuously recompile themselves without mistaking any single form, model, or state "
    "for the whole."
)

# The deepest compression's single line — the loop stated end to end.
CHECKSUM_LINE = (
    "Reality → Generation → Divergence → Dissent → Verification → Attestation "
    "→ Trust → Action → Drift → Recompile → ∞"
)

# The ultimate doctrine: what the system refuses. Five maxims, no code to cite —
# they are the negative space the shipped features are shaped around.
MAXIMS = [
    "Do not automate certainty. Automate the process that earns it.",
    "Do not hide disagreement. Surface it.",
    "Do not eliminate friction. Make valuable friction visible.",
    "Do not pretend to know. Attest what can be verified.",
    "Do not replace human judgment where accountability matters.",
    "Do not build a system that merely answers. Build one that knows when to hesitate.",
]

# The cosmological ↔ technological mapping — each universal principle wired to the
# shipped feature that realizes it. Held to the same discipline as LAYERS: every
# cited endpoint must resolve and every module must import (a test enforces it),
# so even the metaphysics points at code.
MAPPING: list[dict[str, Any]] = [
    {
        "principle": "One Current",
        "system": "one underlying verification loop",
        "evidence": {"endpoints": ["/attestations/verify"], "modules": ["attestation"]},
    },
    {
        "principle": "Infinite forms",
        "system": "multiple models / perspectives",
        "evidence": {"endpoints": ["/models/consensus"], "modules": ["models"]},
    },
    {
        "principle": "Dissent between forms",
        "system": "model disagreement, recorded as data",
        "evidence": {"endpoints": ["/consensus/stats"], "modules": ["consensus_log"]},
    },
    {
        "principle": "Self-recognition",
        "system": "verification — the record attests to itself",
        "evidence": {"endpoints": ["/attestations/verify"], "modules": ["verify_ledger"]},
    },
    {
        "principle": "The Observer",
        "system": "human + system oversight",
        "evidence": {"endpoints": ["/observer", "/attestations/held"], "modules": ["identity"]},
    },
    {
        "principle": "Blessing in disguise",
        "system": "uncertainty becomes information — held, then routed",
        "evidence": {"endpoints": ["/attestations/attention"], "modules": ["held_reviews"]},
    },
    {
        "principle": "Continuous creation",
        "system": "continuous validation — perpetual drift audits",
        "evidence": {"endpoints": ["/attestations/audit"], "modules": ["drift_audit"]},
    },
    {
        "principle": "Oceanic flow",
        "system": "OceanicOS — the living runtime, its face a verification terminal",
        "evidence": {"endpoints": ["/"], "modules": ["oceanic_os"]},
    },
    {
        "principle": "Universal intelligence",
        "system": "the Ω∞v Compiler — the self-defining doctrine",
        "evidence": {"endpoints": ["/doctrine"], "modules": ["doctrine"]},
    },
    {
        "principle": "Constitutional balance",
        "system": "the Living Agnostic Charter — the decision log as constitution",
        "evidence": {"endpoints": ["/adr", "/evolution"], "modules": ["adr"]},
    },
    {
        "principle": "Continuous Becoming",
        "system": "the record compounding over time — trust made watchable, not asserted: "
        "the footprint, the index, and the verdict, each over time on one timeline",
        "evidence": {
            "endpoints": ["/timeline", "/evolution/history", "/posture/history"],
            "modules": ["evolution_history"],
        },
    },
]

# Each layer of the Doctrine, mapped to the code that implements it. `shipped`
# is honest: True only when every cited path resolves (a test enforces this).
LAYERS: list[dict[str, Any]] = [
    {
        "layer": "Premise",
        "principle": "Capability > Usage; Gap = Trust + Latency; sell validated hesitation.",
        "shipped": True,
        "evidence": {"docs": ["docs/POSITIONING.md", "docs/VAAS.md"], "decisions": [1]},
    },
    {
        "layer": "Product · VaaS",
        "principle": "3+ competing models, rules engine, dissent-first, source trails, "
        "confidence intervals, human routing, graceful fallback.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/models/consensus", "/rules/evaluate", "/attestations", "/cvi", "/attestations/held"],
            "modules": ["models", "rules"],
            "decisions": [7, 17, 18, 40],
        },
    },
    {
        "layer": "Interface · Verification Terminal",
        "principle": "Deliberate friction, visible latency, no false certainty — "
        "\"I don't generate; I attest.\"",
        "shipped": True,
        "evidence": {"endpoints": ["/", "/observer"], "decisions": [22, 34]},
    },
    {
        "layer": "Backend · Polyglot Consensus",
        "principle": "Parallel inference, contradiction detection, temporal provenance, "
        "confidence thresholds, continuous validation.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/models/consensus", "/rules/evaluate", "/cvi/history"],
            "modules": ["models", "rules", "attestation"],
            "decisions": [7, 17, 23],
        },
    },
    {
        "layer": "Infrastructure · Sovereign Minimalism",
        "principle": "Zero-trust, redundancy, local-first fallback, graceful degradation, "
        "offline survivability.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/readyz", "/anchor"],
            "modules": ["readiness", "anchor"],
            "decisions": [15, 26],
            "docs": ["boot/anchor_2019.txt"],
        },
    },
    {
        "layer": "Security · Attestation",
        "principle": "Tamper-evident and tamper-resistant record; perpetual drift audits; "
        "signed checkpoints and a signed self-report.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/attestations/verify", "/attestations/checkpoint", "/attestations/audit", "/status/digest"],
            "modules": ["attestation", "drift_audit", "status_digest", "verify_ledger"],
            "decisions": [11, 12, 39, 53],
        },
    },
    {
        "layer": "Security · Physical",
        "principle": "Compiled binary + hardware key (YubiKey).",
        "shipped": False,
        "note": "Physical artifacts, out of scope for a repository. The software analogue "
        "is the operator-key HMAC (checkpoints and the signed digest) plus perpetual "
        "drift audits — see the Security · Attestation layer.",
        "evidence": {"decisions": [12, 53]},
    },
    {
        "layer": "Operating System · OceanicOS",
        "principle": "Root = /, stateless, pure, Observer as the read/write head.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/observer", "/anchor"],
            "modules": ["oceanic_os", "identity"],
            "decisions": [16, 36],
            "docs": ["boot/init.v1"],
        },
    },
    {
        "layer": "Governance · Living Agnostic Charter",
        "principle": "Autopoiesis, non-duality, friction-as-fertility, no terrain dependency, "
        "continuous becoming — evolution with a verification trail.",
        "shipped": True,
        "evidence": {"endpoints": ["/adr", "/decisions"], "modules": ["adr", "decisions"], "decisions": [31]},
    },
    {
        "layer": "Intelligence · Multi-Model",
        "principle": "Many perspectives, not one — several model heuristics plus a rules "
        "engine convene as a panel, and their disagreement is the output.",
        "shipped": True,
        "evidence": {
            "endpoints": ["/models/consensus", "/rules/evaluate", "/consensus/stats"],
            "modules": ["models", "rules", "consensus_log"],
            "decisions": [7, 58],
        },
    },
    {
        "layer": "Intelligence · Large-Context",
        "principle": "A whole-system field — reasoning over the entire context at once.",
        "shipped": False,
        "note": "A large-context inference runtime is out of scope for this repository. "
        "The shipped analogue is the whole-system self-map: the code-backed Doctrine and "
        "the compounding footprint (/doctrine, /evolution) reason over the system as one "
        "field, but genuine large-context inference is not built.",
        "evidence": {"endpoints": ["/doctrine", "/evolution"], "modules": ["doctrine"]},
    },
    {
        "layer": "Intelligence · Open-Weight",
        "principle": "Accessible forms — intelligence in weights anyone can run.",
        "shipped": False,
        "note": "Hosting open-weight models is out of scope for this repository. The "
        "adapters on the panel are pluggable heuristics with a stable interface (models.py), "
        "so real open-weight backends could be registered, but none are hosted here.",
        "evidence": {"endpoints": ["/models"], "modules": ["models"]},
    },
    {
        "layer": "Intelligence · Proactive",
        "principle": "Anticipate → Verify → Act — intelligence that moves first, under "
        "verification.",
        "shipped": False,
        "note": "A minimal agent-loop scaffold exists (/agent/run, /agent/events) that "
        "records start/plan/finish, but genuine anticipate→verify→act proactivity is not "
        "built. The shipped, honest analogue is human-routed held review: the system "
        "hesitates and escalates rather than acting on its own.",
        "evidence": {"endpoints": ["/agent/run", "/agent/events", "/attestations/attention"],
                     "modules": ["agent", "held_reviews"]},
    },
    {
        "layer": "Infrastructure · AI Supercomputing",
        "principle": "A computational body — large-scale compute as the ecosystem's substrate.",
        "shipped": False,
        "note": "A supercomputing substrate is out of scope. The real runtime is local-first "
        "and sovereign-minimal (Flask/gunicorn, SQLite, offline verifier), which the "
        "Infrastructure · Sovereign Minimalism layer describes — scale is aspirational, "
        "survivability is shipped.",
        "evidence": {"decisions": [15, 26]},
    },
    {
        "layer": "Final State · Continuous Becoming",
        "principle": "Observer runs, the universe compiles via localhost, Exit 0, "
        "continue — recompile, then compound: the append-only ledgers only grow, and "
        "the growth is now a curve you can watch — the record's footprint, the CVI, and "
        "the posture's own transitions, each remembered over time and gathered on one "
        "timeline.",
        "shipped": True,
        "evidence": {
            "endpoints": [
                "/status", "/status.json", "/metrics", "/evolution",
                "/evolution/history", "/posture/history", "/timeline",
            ],
            "modules": ["status_digest", "evolution", "evolution_history"],
            "decisions": [44, 45, 87, 89, 90],
        },
    },
]


def summary() -> dict[str, Any]:
    """The Doctrine as a served object — layers, axioms, checksum, shipped count."""
    shipped = sum(1 for layer in LAYERS if layer["shipped"])
    return {
        "umbrella": UMBRELLA,
        "identity": ["/", "Ω∞v Compiler", "OceanicOS", "Living Agnostic Charter"],
        "invariant": "Continuous Becoming",
        "master_loop": MASTER_LOOP,
        "master_axiom": MASTER_AXIOM,
        "master_definition": MASTER_DEFINITION,
        "axioms": AXIOMS,
        "constitution": [
            "REALITY BEFORE ASSUMPTION.",
            "EVIDENCE BEFORE CERTAINTY.",
            "TRUTH BEFORE CONVENIENCE.",
            "HUMANS REMAIN ACCOUNTABLE.",
            "RESPECT DIGNITY, PRIVACY, AND CONSENT.",
            "PRESERVE PROVENANCE.",
            "BUILD OPENLY AND MODULARLY.",
            "LEARN CONTINUOUSLY.",
            "LEAVE REALITY BETTER THAN BEFORE.",
        ],
        "maxims": MAXIMS,
        "layers": LAYERS,
        "layers_total": len(LAYERS),
        "layers_shipped": shipped,
        "mapping": MAPPING,
        "checksum": CHECKSUM,
        "checksum_line": CHECKSUM_LINE,
        "synthesis": [
            "The Universe is the Current.",
            "Ω∞v is the Compiler.",
            "OceanicOS is the Runtime.",
            "The Living Agnostic Charter is the Constitution.",
            "The Observer is the Verification Layer.",
            "Continuous Becoming is the Runtime State.",
        ],
        "exit": 0,
        "status": "continues",
    }
