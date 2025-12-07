"""
Proof Generator for zkML verification.
Generates zero-knowledge proofs for model inference and integrity.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .types import (
    Proof,
    ProofRequest,
    ProofType,
    ProofStatus,
    ModelIntegrityProof,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ProofGenerator:
    """
    Generates zero-knowledge proofs for ML model inference.
    
    In production, this would integrate with zkML libraries like EZKL or Giza.
    For v0.2.0, we implement a proof-of-concept with cryptographic commitments.
    """

    def __init__(self):
        """Initialize the proof generator."""
        self.proof_cache: Dict[str, Proof] = {}
        logger.info("ProofGenerator initialized")

    async def generate_proof(self, request: ProofRequest) -> Proof:
        """
        Generate a zero-knowledge proof for model inference.

        Args:
            request: Proof generation request

        Returns:
            Generated proof

        Raises:
            ValueError: If proof generation fails
        """
        try:
            start_time = time.time()
            logger.info(f"Generating proof for model {request.model_id}")

            # Generate unique proof ID
            proof_id = self._generate_proof_id(request)

            # Generate proof data based on type
            if request.proof_type == ProofType.INFERENCE:
                proof_data = await self._generate_inference_proof(request)
            elif request.proof_type == ProofType.MODEL_INTEGRITY:
                proof_data = await self._generate_model_integrity_proof(request)
            else:
                proof_data = await self._generate_data_integrity_proof(request)

            # Extract public inputs (non-sensitive data that can be verified)
            public_inputs = self._extract_public_inputs(request)

            # Generate verification key
            verification_key = self._generate_verification_key(request.model_id, proof_data)

            # Create proof object
            proof = Proof(
                proof_id=proof_id,
                model_id=request.model_id,
                proof_type=request.proof_type,
                proof_data=proof_data,
                public_inputs=public_inputs,
                timestamp=datetime.utcnow(),
                status=ProofStatus.COMPLETED,
                verification_key=verification_key,
                metadata={
                    "generation_time_ms": (time.time() - start_time) * 1000,
                    "proof_size_bytes": len(proof_data),
                    **(request.metadata or {}),
                },
            )

            # Cache the proof
            self.proof_cache[proof_id] = proof

            logger.info(
                f"Proof generated successfully: {proof_id} "
                f"(took {proof.metadata['generation_time_ms']:.2f}ms)"
            )

            return proof

        except Exception as e:
            logger.error(f"Failed to generate proof: {str(e)}")
            raise ValueError(f"Proof generation failed: {str(e)}")

    async def _generate_inference_proof(self, request: ProofRequest) -> str:
        """
        Generate proof for model inference.
        
        This is a simplified implementation. In production, this would use
        zkML libraries like EZKL to generate actual zero-knowledge proofs.
        
        Args:
            request: Proof request
            
        Returns:
            Hex-encoded proof data
        """
        # Create a commitment to the inference
        commitment_data = {
            "model_id": request.model_id,
            "input_hash": self._hash_data(request.input_data),
            "output_hash": self._hash_data(request.output_data),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Generate cryptographic commitment (simplified)
        commitment = self._hash_data(commitment_data)

        # In production, this would be replaced with actual zkML proof generation
        # using libraries like EZKL or Giza
        proof_data = {
            "commitment": commitment,
            "proof_type": "inference",
            "version": "0.2.0-poc",
        }

        return json.dumps(proof_data).encode().hex()

    async def _generate_model_integrity_proof(self, request: ProofRequest) -> str:
        """
        Generate proof of model integrity.
        
        Args:
            request: Proof request
            
        Returns:
            Hex-encoded proof data
        """
        # Hash the model parameters (in production, this would hash actual model weights)
        model_hash = hashlib.sha256(request.model_id.encode()).hexdigest()

        proof_data = {
            "model_hash": model_hash,
            "proof_type": "model_integrity",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return json.dumps(proof_data).encode().hex()

    async def _generate_data_integrity_proof(self, request: ProofRequest) -> str:
        """
        Generate proof of data integrity.
        
        Args:
            request: Proof request
            
        Returns:
            Hex-encoded proof data
        """
        data_hash = self._hash_data(request.input_data)

        proof_data = {
            "data_hash": data_hash,
            "proof_type": "data_integrity",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return json.dumps(proof_data).encode().hex()

    def _generate_proof_id(self, request: ProofRequest) -> str:
        """Generate unique proof ID."""
        unique_str = f"{request.model_id}_{datetime.utcnow().isoformat()}_{uuid.uuid4()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _hash_data(self, data: Any) -> str:
        """Hash arbitrary data for commitments."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _extract_public_inputs(self, request: ProofRequest) -> Dict[str, Any]:
        """
        Extract public inputs from the request.
        Public inputs are non-sensitive data that can be used for verification.
        """
        return {
            "model_id": request.model_id,
            "proof_type": request.proof_type.value,
            "input_hash": self._hash_data(request.input_data),
            "output_hash": self._hash_data(request.output_data),
        }

    def _generate_verification_key(self, model_id: str, proof_data: str) -> str:
        """Generate verification key for the proof."""
        key_data = f"{model_id}_{proof_data[:32]}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get_proof(self, proof_id: str) -> Optional[Proof]:
        """
        Retrieve a cached proof by ID.
        
        Args:
            proof_id: Proof identifier
            
        Returns:
            Proof if found, None otherwise
        """
        return self.proof_cache.get(proof_id)

    async def generate_model_integrity_proof(self, model_id: str, model_weights: Optional[bytes] = None) -> ModelIntegrityProof:
        """
        Generate a proof of model integrity.
        
        Args:
            model_id: Model identifier
            model_weights: Optional model weights bytes
            
        Returns:
            Model integrity proof
        """
        # Hash model weights (or use model_id if weights not provided)
        if model_weights:
            model_hash = hashlib.sha256(model_weights).hexdigest()
        else:
            model_hash = hashlib.sha256(model_id.encode()).hexdigest()

        # Generate proof
        proof_data = {
            "model_id": model_id,
            "model_hash": model_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return ModelIntegrityProof(
            model_id=model_id,
            model_hash=model_hash,
            proof_data=json.dumps(proof_data).encode().hex(),
            timestamp=datetime.utcnow(),
        )
