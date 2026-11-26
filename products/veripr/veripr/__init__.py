"""VeriPR — Deterministic Proof-of-Verification & AI Anti-Cheat Auditor."""

__version__ = "0.2.0"

from .core import (
    CommandRun,
    Finding,
    Receipt,
    analyze_diff,
    generate_receipt,
    is_test_source_file,
    seal_receipt,
)
from .render import BrandOptions, render_html, render_markdown

__all__ = [
    "__version__",
    "BrandOptions",
    "CommandRun",
    "Finding",
    "Receipt",
    "analyze_diff",
    "generate_receipt",
    "is_test_source_file",
    "render_html",
    "render_markdown",
    "seal_receipt",
]
