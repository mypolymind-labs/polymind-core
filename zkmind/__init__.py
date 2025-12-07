"""
zkMind - Zero-Knowledge Machine Learning Verification Layer
Provides cryptographic proof generation and verification for ML model inference.
"""

from .proof_generator import ProofGenerator
from .verifier import ProofVerifier
from .types import Proof, ProofRequest, VerificationResult

__all__ = [
    "ProofGenerator",
    "ProofVerifier",
    "Proof",
    "ProofRequest",
    "VerificationResult",
]
