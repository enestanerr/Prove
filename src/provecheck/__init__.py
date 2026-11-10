"""Prove: audit every checkable claim in a document. Verdicts come from code."""

__version__ = "0.1.0"

VERIFIED = "verified"
CONTRADICTED = "contradicted"
SUSPECT = "suspect"
UNVERIFIED = "unverified"
SKIPPED = "skipped"

VERDICTS = (CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED, SKIPPED)
