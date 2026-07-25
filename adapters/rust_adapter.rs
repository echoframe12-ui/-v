//! Reference Rust adapter for the Ω∞ Oceanic verification compiler.
//!
//! This adapter demonstrates a second implementation perspective over the
//! same Oceanic IR contract. Rust's checked arithmetic makes overflow handling
//! explicit, while the verifier still treats the emitted proof as evidence
//! rather than assuming the language itself proves the entire contract.

use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CombineError {
    Overflow,
}

impl fmt::Display for CombineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CombineError::Overflow => write!(f, "integer overflow"),
        }
    }
}

/// Contract implementation: combine two signed integers without silently
/// accepting overflow.
pub fn combine(a: i64, b: i64) -> Result<i64, CombineError> {
    a.checked_add(b).ok_or(CombineError::Overflow)
}

#[cfg(test)]
mod tests {
    use super::{combine, CombineError};

    #[test]
    fn combines_values() {
        assert_eq!(combine(2, 3), Ok(5));
    }

    #[test]
    fn surfaces_overflow() {
        assert_eq!(combine(i64::MAX, 1), Err(CombineError::Overflow));
    }

    #[test]
    fn handles_negative_values() {
        assert_eq!(combine(-5, 3), Ok(-2));
    }
}

/// The adapter's proof manifest is represented as data so the core verifier
/// can consume the same semantic evidence format used by other adapters.
pub const ADAPTER_LANGUAGE: &str = "rust";
pub const ADAPTER_PROTOCOL: &str = "oceanic.adapter/v0.1";
pub const ADAPTER_VERSION: &str = "0.1.0";
pub const CAPABILITIES: &[&str] = &[
    "arithmetic_correctness",
    "overflow_handling",
    "memory_safety",
];
pub const PROOF_TYPES: &[&str] = &["compiler_checks", "checked_arithmetic", "unit_tests"];
pub const LIMITATIONS: &[&str] = &[
    "platform and toolchain assumptions must be recorded",
    "unsafe code requires explicit additional dissent",
];
