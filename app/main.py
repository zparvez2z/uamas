import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from reliable_genai.catalog_quality_graph import CatalogQualityGraph
from reliable_genai.models import (
    CatalogQualityDecision,
    ListingInput,
    OperationalMetrics,
    ProductInput,
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
catalog_quality_graph = CatalogQualityGraph(pipeline, review_graph, review_store)
RESULTS_JSON_PATH = Path("reports/results.json")
RESULTS_MD_PATH = Path("reports/results.md")


def current_catalog_quality_graph() -> CatalogQualityGraph:
    return catalog_quality_graph


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
    catalog_graph_diagnostics = current_catalog_quality_graph().diagnostics()
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
        "catalog_quality_graph_available": catalog_graph_diagnostics.get("available"),
        "catalog_quality_graph_backend": catalog_graph_diagnostics.get("backend"),
        "catalog_quality_graph_reason": catalog_graph_diagnostics.get("reason"),
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


def build_operational_metrics() -> OperationalMetrics:
    persistence_metrics = review_store.metrics()
    semantic_scorer = getattr(pipeline, "semantic_scorer", None)
    semantic_diagnostics = (
        semantic_scorer.diagnostics()
        if semantic_scorer is not None and hasattr(semantic_scorer, "diagnostics")
        else {"degraded_rate": 0.0, "degraded_requests": 0}
    )
    review_diagnostics = review_graph.diagnostics()
    return OperationalMetrics(
        status="ok" if persistence_metrics["available"] else "degraded",
        persistence_available=bool(persistence_metrics["available"]),
        persistence_db_path=str(persistence_metrics["db_path"]),
        persistence_error=persistence_metrics.get("error"),
        listing_count=int(persistence_metrics["listing_count"]),
        prediction_count=int(persistence_metrics["prediction_count"]),
        review_task_count=int(persistence_metrics["review_task_count"]),
        pending_review_task_count=int(persistence_metrics["pending_review_task_count"]),
        approved_review_task_count=int(persistence_metrics["approved_review_task_count"]),
        corrected_review_task_count=int(persistence_metrics["corrected_review_task_count"]),
        rejected_review_task_count=int(persistence_metrics["rejected_review_task_count"]),
        review_status_counts=dict(persistence_metrics["review_status_counts"]),
        review_reason_counts=dict(persistence_metrics["review_reason_counts"]),
        auto_accept_count=int(persistence_metrics["auto_accept_count"]),
        needs_human_review_count=int(persistence_metrics["needs_human_review_count"]),
        auto_accept_rate=float(persistence_metrics["auto_accept_rate"]),
        human_review_rate=float(persistence_metrics["human_review_rate"]),
        correction_rate=float(persistence_metrics["correction_rate"]),
        semantic_degraded_rate=float(semantic_diagnostics.get("degraded_rate", 0.0)),
        semantic_degraded_requests=int(semantic_diagnostics.get("degraded_requests", 0)),
        llm_runtime_mode="MOCK" if pipeline.llm.use_mock else "LIVE",
        llm_last_runtime=pipeline.llm.last_runtime,
        llm_last_error=pipeline.llm.last_error,
        classifier_runtime=str(pipeline.classifier.diagnostics().get("runtime")),
        review_graph_trigger_rate=review_diagnostics.get("review_graph_trigger_rate"),
        review_graph_second_pass_rate=review_diagnostics.get("review_graph_second_pass_rate"),
    )


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


@app.get("/api/metrics", response_model=OperationalMetrics)
def api_metrics() -> OperationalMetrics:
    return build_operational_metrics()


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
    return current_catalog_quality_graph().analyze(listing)


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
    metrics_payload = build_operational_metrics()
    artifact, artifact_error = load_results_artifact()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "diagnostics": diagnostics_payload,
            "metrics": metrics_payload,
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
