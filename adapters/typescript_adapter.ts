/**
 * Reference TypeScript adapter for the Ω∞ Oceanic verification compiler.
 *
 * Same contract, different execution model. The adapter deliberately surfaces
 * JavaScript number semantics as a limitation instead of claiming arbitrary
 * integer safety.
 */

export const MANIFEST = {
  protocol: "oceanic.adapter/v0.1",
  language: "typescript",
  languageVersion: "5.x",
  adapterVersion: "0.1.0",
  capabilities: ["arithmetic_correctness", "runtime_checks", "pure_functions"],
  proofTypes: ["typecheck", "unit_tests", "static_analysis"],
  limitations: [
    "number uses IEEE-754 floating-point semantics",
    "arbitrary integer precision requires explicit bigint domain",
  ],
  localFirst: true,
  dissentMode: "surface_first",
} as const;

export type CombineResult =
  | { ok: true; value: number }
  | { ok: false; error: "unsafe_integer" };

/**
 * Contract implementation for the declared safe-integer domain.
 * Values outside Number's safe integer range are rejected rather than
 * silently rounded.
 */
export function combine(a: number, b: number): CombineResult {
  const result = a + b;

  if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b)) {
    return { ok: false, error: "unsafe_integer" };
  }

  if (!Number.isSafeInteger(result)) {
    return { ok: false, error: "unsafe_integer" };
  }

  return { ok: true, value: result };
}

export const PROOF_CLAIMS = [
  {
    obligation: "arithmetic_correctness",
    status: "satisfied",
    evidenceType: "unit_tests",
  },
  {
    obligation: "overflow_handling",
    status: "satisfied_with_domain_constraint",
    evidenceType: "Number.isSafeInteger",
  },
] as const;
