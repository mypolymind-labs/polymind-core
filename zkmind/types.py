"""
Type definitions for zkMind module.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProofType(str, Enum):
    """Types of proofs that can be generated."""
    INFERENCE = "inference"
    MODEL_INTEGRITY = "model_integrity"
    DATA_INTEGRITY = "data_integrity"


class ProofStatus(str, Enum):
    """Status of proof generation/verification."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ProofRequest(BaseModel):
    """Request for proof generation."""
    model_id: str = Field(..., description="Unique identifier for the model")
    input_data: Dict[str, Any] = Field(..., description="Input data for inference")
    output_data: Dict[str, Any] = Field(..., description="Output from model inference")
    proof_type: ProofType = Field(default=ProofType.INFERENCE, description="Type of proof to generate")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class Proof(BaseModel):
    """Zero-knowledge proof for ML inference."""
    proof_id: str = Field(..., description="Unique identifier for this proof")
    model_id: str = Field(..., description="Model that generated the prediction")
    proof_type: ProofType = Field(..., description="Type of proof")
    proof_data: str = Field(..., description="Serialized proof data (hex encoded)")
    public_inputs: Dict[str, Any] = Field(..., description="Public inputs to the proof")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When proof was generated")
    status: ProofStatus = Field(default=ProofStatus.COMPLETED, description="Status of the proof")
    verification_key: Optional[str] = Field(default=None, description="Verification key for this proof")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VerificationResult(BaseModel):
    """Result of proof verification."""
    proof_id: str = Field(..., description="ID of the proof being verified")
    is_valid: bool = Field(..., description="Whether the proof is valid")
    verified_at: datetime = Field(default_factory=datetime.utcnow, description="When verification occurred")
    error: Optional[str] = Field(default=None, description="Error message if verification failed")
    verification_time_ms: Optional[float] = Field(default=None, description="Time taken to verify (milliseconds)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional verification metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ModelIntegrityProof(BaseModel):
    """Proof of model integrity - ensures model hasn't been tampered with."""
    model_id: str = Field(..., description="Model identifier")
    model_hash: str = Field(..., description="Hash of the model weights")
    proof_data: str = Field(..., description="ZK proof of model integrity")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProofStorage(BaseModel):
    """Storage record for on-chain proof."""
    proof_id: str
    chain: str = Field(..., description="Blockchain where proof is stored")
    transaction_hash: str = Field(..., description="Transaction hash of proof storage")
    block_number: int = Field(..., description="Block number where proof was stored")
    contract_address: Optional[str] = Field(default=None, description="Smart contract address")
    storage_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
