from typing import Dict, List, Literal, Optional

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
    classifier_artifact_load_attempted: bool = False
    classifier_artifact_load_status: str = "not_attempted"
    classifier_artifact_rejection_reason: Optional[str] = None
    classifier_artifact_rebuild_attempted: bool = False
    classifier_artifact_rebuild_status: str = "not_needed"
    classifier_artifact_rebuild_reason: Optional[str] = None
    semantic_consistency_score: Optional[float] = None
    semantic_consistency_status: str = "disabled"
    semantic_consistency_reason: Optional[str] = None
    review_graph_used: bool = False
    review_trigger_reason: Optional[str] = None
    review_outcome: Optional[str] = None
    coverage_threshold: float


class PredictionResponse(BaseModel):
    category_set: List[str]
    attributes: ProductAttributes
    reliability: ReliabilityMeta


class ListingInput(ProductInput):
    external_id: Optional[str] = None


class AgentTrace(BaseModel):
    agent: str
    status: str
    output: Dict[str, object] = Field(default_factory=dict)
    reason: Optional[str] = None


class CatalogQualityDecision(BaseModel):
    listing_id: str
    decision: Literal["auto_accept", "needs_human_review", "reject_or_request_clarification"]
    risk_level: Literal["low", "medium", "high"]
    explanation: str
    category_set: List[str]
    attributes: ProductAttributes
    reliability: ReliabilityMeta
    agent_trace: List[AgentTrace] = Field(default_factory=list)
    review_task_id: Optional[str] = None


class ReviewTask(BaseModel):
    id: str
    listing_id: str
    prediction_id: Optional[str] = None
    status: Literal["pending", "approved", "corrected", "rejected"] = "pending"
    reason: str
    risk_level: Literal["low", "medium", "high"] = "high"
    corrected_category: Optional[str] = None
    corrected_attributes: Dict[str, object] = Field(default_factory=dict)
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class ReviewQueueItem(ReviewTask):
    title: str
    description: str = ""


class ReviewDecision(BaseModel):
    action: Literal["approve", "correct", "reject"]
    corrected_category: Optional[str] = None
    corrected_attributes: Dict[str, object] = Field(default_factory=dict)
    notes: Optional[str] = None


class LLMExtraction(BaseModel):
    attributes: ProductAttributes
    notes: Optional[str] = None


class ClassifierResult(BaseModel):
    probabilities: Dict[str, float]
    sorted_labels: List[str]
