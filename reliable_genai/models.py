from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(default="")


class ProductAttributes(BaseModel):
    brand: str = "unknown"
    color: str = "unknown"
    material: str = "unknown"
    size: str = "unknown"


class ReliabilityMeta(BaseModel):
    alpha: float
    coverage_target: float
    set_size: int
    confidence: float
    abstained: bool
    reason: Optional[str] = None
    policy_action: str
    llm_runtime: str
    llm_model: str
    classifier_runtime: str
    classifier_reason: Optional[str] = None
    classifier_artifact_path: Optional[str] = None
    classifier_model_type: Optional[str] = None
    coverage_threshold: float


class PredictionResponse(BaseModel):
    category_set: List[str]
    attributes: ProductAttributes
    reliability: ReliabilityMeta


class LLMExtraction(BaseModel):
    attributes: ProductAttributes
    notes: Optional[str] = None


class ClassifierResult(BaseModel):
    probabilities: Dict[str, float]
    sorted_labels: List[str]
