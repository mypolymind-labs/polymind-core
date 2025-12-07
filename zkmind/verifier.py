"""
Proof Verifier for zkML verification.
Verifies zero-knowledge proofs for model inference and integrity.
"""

import json
import time
import hashlib
from typing import Optional
from datetime import datetime

from .types import Proof, VerificationResult, ProofStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class ProofVerifier:
    """
    Verifies zero-knowledge proofs for ML model inference.
    
    In production, this would integrate with zkML verification libraries.
    For v0.2.0, we implement a proof-of-concept verifier.
    """

    def __init__(self):
        """Initialize the proof verifier."""
        self.verification_cache: dict[str, VerificationResult] = {}
        logger.info("ProofVerifier initialized")

    async def verify_proof(self, proof: Proof) -> VerificationResult:
        """
        Verify a zero-knowledge proof.

        Args:
            proof: Proof to verify

        Returns:
            Verification result
        """
        try:
            start_time = time.time()
            logger.info(f"Verifying proof {proof.proof_id}")

            # Check if already verified
            if proof.proof_id in self.verification_cache:
                logger.info(f"Proof {proof.proof_id} already verified (cached)")
                return self.verification_cache[proof.proof_id]

            # Verify proof based on type
            is_valid = await self._verify_proof_data(proof)

            # Calculate verification time
            verification_time_ms = (time.time() - start_time) * 1000

            # Create verification result
            result = VerificationResult(
                proof_id=proof.proof_id,
                is_valid=is_valid,
                verified_at=datetime.utcnow(),
                error=None if is_valid else "Proof verification failed",
                verification_time_ms=verification_time_ms,
                metadata={
                    "proof_type": proof.proof_type.value,
                    "model_id": proof.model_id,
                },
            )

            # Cache the result
            self.verification_cache[proof.proof_id] = result

            logger.info(
                f"Proof verification {'succeeded' if is_valid else 'failed'}: {proof.proof_id} "
                f"(took {verification_time_ms:.2f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to verify proof {proof.proof_id}: {str(e)}")
            return VerificationResult(
                proof_id=proof.proof_id,
                is_valid=False,
                verified_at=datetime.utcnow(),
                error=f"Verification error: {str(e)}",
                verification_time_ms=None,
            )

    async def _verify_proof_data(self, proof: Proof) -> bool:
        """
        Verify the proof data.
        
        This is a simplified implementation. In production, this would use
        zkML verification libraries to verify actual zero-knowledge proofs.
        
        Args:
            proof: Proof to verify
            
        Returns:
            True if proof is valid, False otherwise
        """
        try:
            # Decode proof data
            proof_bytes = bytes.fromhex(proof.proof_data)
            proof_dict = json.loads(proof_bytes.decode())

            # Basic validation
            if "proof_type" not in proof_dict:
                return False

            # Verify proof type matches
            if proof_dict["proof_type"] != proof.proof_type.value:
                return False

            # Verify verification key if present
            if proof.verification_key:
                expected_key = self._generate_verification_key(proof.model_id, proof.proof_data)
                if proof.verification_key != expected_key:
                    logger.warning(f"Verification key mismatch for proof {proof.proof_id}")
                    return False

            # In production, this would perform actual zkML verification
            # For now, we just verify the structure and consistency
            return True

        except Exception as e:
            logger.error(f"Error verifying proof data: {str(e)}")
            return False

    def _generate_verification_key(self, model_id: str, proof_data: str) -> str:
        """Generate verification key (must match ProofGenerator implementation)."""
        key_data = f"{model_id}_{proof_data[:32]}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def verify_public_inputs(self, proof: Proof, expected_inputs: dict) -> bool:
        """
        Verify that public inputs match expected values.
        
        Args:
            proof: Proof to verify
            expected_inputs: Expected public input values
            
        Returns:
            True if inputs match, False otherwise
        """
        try:
            for key, expected_value in expected_inputs.items():
                if key not in proof.public_inputs:
                    logger.warning(f"Missing public input: {key}")
                    return False
                
                if proof.public_inputs[key] != expected_value:
                    logger.warning(f"Public input mismatch for {key}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error verifying public inputs: {str(e)}")
            return False

    def get_verification_result(self, proof_id: str) -> Optional[VerificationResult]:
        """
        Retrieve a cached verification result.
        
        Args:
            proof_id: Proof identifier
            
        Returns:
            Verification result if found, None otherwise
        """
        return self.verification_cache.get(proof_id)

    async def batch_verify(self, proofs: list[Proof]) -> list[VerificationResult]:
        """
        Verify multiple proofs in batch.
        
        Args:
            proofs: List of proofs to verify
            
        Returns:
            List of verification results
        """
        results = []
        for proof in proofs:
            result = await self.verify_proof(proof)
            results.append(result)
        
        return results

    def clear_cache(self):
        """Clear the verification cache."""
        self.verification_cache.clear()
        logger.info("Verification cache cleared")
