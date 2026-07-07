import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from reliable_genai.models import (
    AgentTrace,
    CatalogQualityDecision,
    ListingInput,
    ProductInput,
    PredictionResponse,
    ReviewDecision,
    ReviewQueueItem,
    ReviewTask,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.pipeline import ReliabilityPipeline
from reliable_genai.review_graph import ReviewGraphRunner

load_dotenv()

app = FastAPI(title="Reliable GenAI Demo")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

pipeline = ReliabilityPipeline()
review_graph = ReviewGraphRunner(pipeline)
review_store = SQLiteReviewStore()
RESULTS_JSON_PATH = Path("reports/results.json")
RESULTS_MD_PATH = Path("reports/results.md")


def review_confidence_threshold() -> float:
    return float(os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.55"))


def semantic_consistency_threshold() -> float:
    diagnostics_payload = review_graph.diagnostics()
    threshold = diagnostics_payload.get("semantic_threshold")
    if threshold is not None:
        return float(threshold)
    return float(os.getenv("SEMANTIC_CONSISTENCY_THRESHOLD", "0.4"))


def review_decision_for_prediction(prediction: PredictionResponse) -> tuple[str, str, str | None, str]:
    reliability = prediction.reliability
    semantic_score = reliability.semantic_consistency_score
    semantic_threshold = semantic_consistency_threshold()

    if reliability.abstained or not prediction.category_set:
        reason = reliability.reason or reliability.review_trigger_reason or "abstained"
        return "needs_human_review", "high", reason, "Classifier abstained or returned no category set."

    max_auto_accept_set_size = int(os.getenv("MAX_AUTO_ACCEPT_SET_SIZE", str(pipeline.max_set_size)))
    if len(prediction.category_set) > max_auto_accept_set_size:
        return "needs_human_review", "high", "large_set", "Category set is too large for automatic acceptance."

    if reliability.confidence < review_confidence_threshold():
        return "needs_human_review", "high", "low_confidence", "Classifier confidence is below review threshold."

    if (
        reliability.semantic_consistency_status == "ok"
        and semantic_score is not None
        and semantic_score < semantic_threshold
    ):
        return (
            "needs_human_review",
            "high",
            "low_semantic_consistency",
            "Semantic consistency score is below review threshold.",
        )

    risk_level = "low" if len(prediction.category_set) == 1 else "medium"
    return "auto_accept", risk_level, None, "Listing passed automatic catalog quality checks."


def build_agent_trace(
    prediction: PredictionResponse,
    *,
    decision: str,
    risk_level: str,
    review_reason: str | None,
    review_task_id: str | None,
) -> list[AgentTrace]:
    reliability = prediction.reliability
    semantic_threshold = semantic_consistency_threshold()
    return [
        AgentTrace(
            agent="classifier_agent",
            status="ok",
            output={
                "category_set": prediction.category_set,
                "confidence": reliability.confidence,
                "set_size": len(prediction.category_set),
                "abstained": reliability.abstained,
            },
            reason=reliability.reason,
        ),
        AgentTrace(
            agent="attribute_extraction_agent",
            status="ok",
            output=prediction.attributes.model_dump(),
            reason=None,
        ),
        AgentTrace(
            agent="semantic_critic_agent",
            status=reliability.semantic_consistency_status,
            output={
                "score": reliability.semantic_consistency_score,
                "threshold": semantic_threshold,
            },
            reason=reliability.semantic_consistency_reason,
        ),
        AgentTrace(
            agent="policy_agent",
            status="ok",
            output={
                "decision": decision,
                "risk_level": risk_level,
            },
            reason=review_reason,
        ),
        AgentTrace(
            agent="human_review_agent",
            status="created" if review_task_id else "skipped",
            output={"review_task_id": review_task_id},
            reason=review_reason,
        ),
    ]


def build_diagnostics() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    classifier_diagnostics = pipeline.classifier.diagnostics()
    semantic_scorer = getattr(pipeline, "semantic_scorer", None)
    if semantic_scorer is not None and hasattr(semantic_scorer, "diagnostics"):
        semantic_diagnostics = semantic_scorer.diagnostics()
    else:
        semantic_diagnostics = {
            "enabled": False,
            "client_available": False,
            "threshold": None,
            "model": None,
            "degraded_rate": 0.0,
            "degraded_requests": 0,
        }
    review_diagnostics = review_graph.diagnostics()
    persistence_diagnostics = review_store.diagnostics()
    artifact_metadata = classifier_diagnostics.get("artifact_metadata", {}) or {}
    return {
        "status": "ok",
        "runtime_mode": "MOCK" if pipeline.llm.use_mock else "LIVE",
        "model": pipeline.llm.model,
        "endpoint": pipeline.llm.endpoint,
        "token_present": bool(token),
        "token_prefix": token[:8] + "..." if token else None,
        "last_runtime": pipeline.llm.last_runtime,
        "llm_last_error": pipeline.llm.last_error,
        "classifier_runtime": classifier_diagnostics["runtime"],
        "classifier_ready": classifier_diagnostics["ready"],
        "classifier_reason": classifier_diagnostics["reason"],
        "classifier_artifact_path": classifier_diagnostics["artifact_path"],
        "classifier_model_type": classifier_diagnostics.get("model_type"),
        "classifier_artifact_load_attempted": classifier_diagnostics.get("artifact_load_attempted", False),
        "classifier_artifact_load_status": classifier_diagnostics.get("artifact_load_status", "not_attempted"),
        "classifier_artifact_rejection_reason": classifier_diagnostics.get("artifact_rejection_reason"),
        "classifier_artifact_rebuild_attempted": classifier_diagnostics.get("artifact_rebuild_attempted", False),
        "classifier_artifact_rebuild_status": classifier_diagnostics.get("artifact_rebuild_status", "not_needed"),
        "classifier_artifact_rebuild_reason": classifier_diagnostics.get("artifact_rebuild_reason"),
        "coverage_threshold": classifier_diagnostics["coverage_threshold"],
        "classifier_artifact_metadata": artifact_metadata,
        "classifier_artifact_format_version": artifact_metadata.get("artifact_format_version"),
        "classifier_dataset_fingerprint": artifact_metadata.get("dataset_fingerprint_sha256"),
        "review_graph_enabled": review_diagnostics.get("enabled"),
        "review_graph_available": review_diagnostics.get("available"),
        "review_graph_backend": review_diagnostics.get("backend"),
        "review_graph_reason": review_diagnostics.get("reason"),
        "review_graph_confidence_threshold": review_diagnostics.get("confidence_threshold"),
        "review_graph_set_size_trigger": review_diagnostics.get("set_size_trigger"),
        "review_graph_semantic_threshold": review_diagnostics.get("semantic_threshold"),
        "review_graph_gate_strategy": review_diagnostics.get("gate_strategy"),
        "review_graph_very_low_confidence_floor": review_diagnostics.get("very_low_confidence_floor"),
        "review_graph_trigger_rate": review_diagnostics.get("review_graph_trigger_rate"),
        "review_graph_second_pass_rate": review_diagnostics.get("review_graph_second_pass_rate"),
        "review_graph_semantic_trigger_rate": review_diagnostics.get("review_graph_semantic_trigger_rate"),
        "review_graph_cache_hit_rate": review_diagnostics.get("review_graph_cache_hit_rate"),
        "review_graph_cached_step_count": review_diagnostics.get("review_graph_cached_step_count"),
        "semantic_scorer_enabled": semantic_diagnostics.get("enabled"),
        "semantic_scorer_client_available": semantic_diagnostics.get("client_available"),
        "semantic_scorer_threshold": semantic_diagnostics.get("threshold"),
        "semantic_scorer_model": semantic_diagnostics.get("model"),
        "semantic_scorer_degraded_rate": semantic_diagnostics.get("degraded_rate"),
        "semantic_scorer_degraded_requests": semantic_diagnostics.get("degraded_requests"),
        "persistence_available": persistence_diagnostics.get("available"),
        "persistence_db_path": persistence_diagnostics.get("db_path"),
        "persistence_error": persistence_diagnostics.get("error"),
        "listing_count": persistence_diagnostics.get("listing_count"),
        "review_task_count": persistence_diagnostics.get("review_task_count"),
        "pending_review_task_count": persistence_diagnostics.get("pending_review_task_count"),
    }


def load_results_artifact(path: Path = RESULTS_JSON_PATH) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"{path} not found"
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as exc:
        return None, f"failed to parse {path}: {exc}"


def parse_corrected_attributes(raw: str | None) -> dict[str, object]:
    if raw is None or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"corrected_attributes_json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="corrected_attributes_json must be a JSON object")
    return parsed


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": None,
            "title": "",
            "description": "",
            "error": None,
            "runtime": "MOCK" if pipeline.llm.use_mock else "LIVE",
            "model": pipeline.llm.model,
            "diagnostics": build_diagnostics(),
        },
    )


@app.post("/predict", response_class=HTMLResponse)
def predict(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
) -> HTMLResponse:
    try:
        payload = ProductInput(title=title, description=description)
        prediction = review_graph.predict(payload)
        result_json = json.dumps(prediction.model_dump(), indent=2)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "result": result_json,
                "title": title,
                "description": description,
                "error": None,
                "runtime": prediction.reliability.llm_runtime,
                "model": prediction.reliability.llm_model,
                "diagnostics": build_diagnostics(),
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "result": None,
                "title": title,
                "description": description,
                "error": str(exc),
                "runtime": "MOCK" if pipeline.llm.use_mock else "LIVE",
                "model": pipeline.llm.model,
                "diagnostics": build_diagnostics(),
            },
            status_code=400,
        )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/diagnostics")
def diagnostics() -> dict:
    return build_diagnostics()


@app.get("/review", response_class=HTMLResponse)
def review_queue_page(request: Request, status: str = "pending", limit: int = 100) -> HTMLResponse:
    selected_status = None if status == "all" else status
    try:
        tasks = review_store.list_review_tasks(status=selected_status, limit=limit)
        error = None
    except ValueError as exc:
        tasks = []
        error = str(exc)
    return templates.TemplateResponse(
        request,
        "review.html",
        {
            "tasks": tasks,
            "status": status,
            "limit": limit,
            "error": error,
            "diagnostics": build_diagnostics(),
        },
    )


@app.post("/review/{task_id}/decision")
def submit_review_task_decision(
    task_id: str,
    action: str = Form(...),
    corrected_category: str = Form(""),
    corrected_attributes_json: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    corrected_attributes = parse_corrected_attributes(corrected_attributes_json)
    decision = ReviewDecision(
        action=action,
        corrected_category=corrected_category.strip() or None,
        corrected_attributes=corrected_attributes,
        notes=notes.strip() or None,
    )
    try:
        review_store.record_review_decision(task_id, decision)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(url="/review", status_code=303)


@app.post("/api/listings/analyze", response_model=CatalogQualityDecision)
def analyze_listing(listing: ListingInput) -> CatalogQualityDecision:
    payload = ProductInput(title=listing.title, description=listing.description)
    prediction = review_graph.predict(payload)
    listing_id = review_store.create_listing(listing)
    prediction_id = review_store.create_prediction(listing_id, prediction)
    decision, risk_level, review_reason, explanation = review_decision_for_prediction(prediction)

    review_task_id = None
    if decision == "needs_human_review":
        task = review_store.create_review_task(
            listing_id=listing_id,
            prediction_id=prediction_id,
            reason=review_reason or "needs_human_review",
            risk_level=risk_level,
        )
        review_task_id = task.id

    return CatalogQualityDecision(
        listing_id=listing_id,
        decision=decision,
        risk_level=risk_level,
        explanation=explanation,
        category_set=prediction.category_set,
        attributes=prediction.attributes,
        reliability=prediction.reliability,
        agent_trace=build_agent_trace(
            prediction,
            decision=decision,
            risk_level=risk_level,
            review_reason=review_reason,
            review_task_id=review_task_id,
        ),
        review_task_id=review_task_id,
    )


@app.get("/api/review-queue", response_model=list[ReviewQueueItem])
def list_review_queue(status: str = "pending", limit: int = 100) -> list[ReviewQueueItem]:
    try:
        return review_store.list_review_tasks(status=status or None, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/review-queue/{task_id}", response_model=ReviewTask)
def get_review_task(task_id: str) -> ReviewTask:
    task = review_store.get_review_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"review task not found: {task_id}")
    return task


@app.post("/api/review-queue/{task_id}/decision", response_model=ReviewTask)
def record_review_task_decision(task_id: str, decision: ReviewDecision) -> ReviewTask:
    try:
        return review_store.record_review_decision(task_id, decision)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    diagnostics_payload = build_diagnostics()
    artifact, artifact_error = load_results_artifact()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "diagnostics": diagnostics_payload,
            "artifact": artifact,
            "artifact_error": artifact_error,
        },
    )


@app.get("/artifacts/results.json")
def artifact_results_json() -> FileResponse:
    if not RESULTS_JSON_PATH.exists():
        raise HTTPException(status_code=404, detail=f"{RESULTS_JSON_PATH} not found")
    return FileResponse(RESULTS_JSON_PATH, media_type="application/json", filename="results.json")


@app.get("/artifacts/results.md")
def artifact_results_md() -> FileResponse:
    if not RESULTS_MD_PATH.exists():
        raise HTTPException(status_code=404, detail=f"{RESULTS_MD_PATH} not found")
    return FileResponse(RESULTS_MD_PATH, media_type="text/markdown", filename="results.md")
