"""Deterministic structural control plane for Reliance Compiler.

This package deliberately does not acquire evidence or perform semantic
reasoning. It validates model-produced packets, recomputes bounded plans, and
reports fixture-scoped comparisons and metrics.
"""

from .engine import (
    ValidationResult,
    compare_packets,
    compute_plan,
    evaluate_directory,
    render_receipt,
    validate_policy,
    validate_packet,
)

__all__ = [
    "ValidationResult",
    "compare_packets",
    "compute_plan",
    "evaluate_directory",
    "render_receipt",
    "validate_policy",
    "validate_packet",
]
