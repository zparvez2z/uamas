import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from reliable_genai.catalog_quality_graph import CatalogQualityGraph
from reliable_genai.models import (
    AgentRun,
    CatalogQualityDecision,
    ListingInput,
    OperationalMetrics,
    ProductInput,
    ReviewDecision,
    ReviewQueueItem,
    ReviewTask,
    WorkflowRun,
    WorkflowRunDetail,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.pipeline import ReliabilityPipeline
from reliable_genai.review_graph import ReviewGraphRunner
from reliable_genai.security import (
    AdminLoginRequired,
    SecurityManager,
    SecuritySettings,
)

load_dotenv()

security = SecurityManager(SecuritySettings.from_env())
app = FastAPI(
    title="UAMAS Catalog Quality Assistant",
    docs_url="/docs" if security.settings.docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if security.settings.docs_enabled else None,
)
if security.settings.allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(security.settings.allowed_hosts),
    )
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

pipeline = ReliabilityPipeline()
review_graph = ReviewGraphRunner(pipeline)
review_store = SQLiteReviewStore()
catalog_quality_graph = CatalogQualityGraph(pipeline, review_graph, review_store)
RESULTS_JSON_PATH = Path("reports/results.json")
RESULTS_MD_PATH = Path("reports/results.md")


def require_admin_access(request: Request) -> None:
    security.require_admin(request)


def require_api_access(request: Request) -> None:
    security.require_api(request)


def require_operator_access(request: Request) -> None:
    security.require_operator(request)


async def require_csrf_form(request: Request) -> None:
    await security.require_csrf(request)


@app.exception_handler(AdminLoginRequired)
def admin_login_required(
    _request: Request,
    exc: AdminLoginRequired,
) -> RedirectResponse:
    return RedirectResponse(
        url=security.login_redirect(exc.next_path),
        status_code=303,
    )


@app.middleware("http")
async def apply_security_controls(request: Request, call_next):
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    sensitive = not (
        request.url.path == "/health"
        or request.url.path.startswith("/static/")
        or request.url.path.startswith("/admin/login")
    )

    def finalize(response):
        security.add_response_headers(response, sensitive=sensitive)
        response.headers["X-Request-ID"] = request_id
        return response

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            too_large = int(content_length) > security.settings.max_request_bytes
        except ValueError:
            return finalize(
                JSONResponse(
                    {"detail": "invalid Content-Length"},
                    status_code=400,
                )
            )
        if too_large:
            return finalize(
                JSONResponse(
                    {"detail": "request body too large"},
                    status_code=413,
                )
            )

    response = await call_next(request)
    return finalize(response)


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
        "security_environment": security.settings.environment,
        "authentication_enabled": security.enabled,
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
        "workflow_run_count": persistence_diagnostics.get("workflow_run_count"),
        "failed_workflow_run_count": persistence_diagnostics.get("failed_workflow_run_count"),
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
        workflow_run_count=int(persistence_metrics["workflow_run_count"]),
        completed_workflow_run_count=int(persistence_metrics["completed_workflow_run_count"]),
        failed_workflow_run_count=int(persistence_metrics["failed_workflow_run_count"]),
        running_workflow_run_count=int(persistence_metrics["running_workflow_run_count"]),
        workflow_success_rate=float(persistence_metrics["workflow_success_rate"]),
        average_workflow_duration_ms=float(persistence_metrics["average_workflow_duration_ms"]),
        p95_workflow_duration_ms=float(persistence_metrics["p95_workflow_duration_ms"]),
        degraded_agent_run_count=int(persistence_metrics["degraded_agent_run_count"]),
        failed_agent_run_count=int(persistence_metrics["failed_agent_run_count"]),
        average_agent_duration_ms=dict(persistence_metrics["average_agent_duration_ms"]),
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


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(
    request: Request,
    next: str = "/",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None,
            "next_path": security.safe_next_path(next),
        },
    )


@app.post("/admin/login", response_model=None)
def admin_login(
    request: Request,
    admin_token: str = Form(...),
    next_path: str = Form("/"),
) -> RedirectResponse | HTMLResponse:
    safe_next = security.safe_next_path(next_path)
    if not security.authenticate_admin_token(admin_token):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Invalid administrator token.",
                "next_path": safe_next,
            },
            status_code=401,
        )
    response = RedirectResponse(url=safe_next, status_code=303)
    security.issue_admin_cookie(response)
    return response


@app.post(
    "/admin/logout",
    dependencies=[Depends(require_admin_access), Depends(require_csrf_form)],
)
def admin_logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=303)
    security.clear_admin_cookie(response)
    return response


@app.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access)],
)
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
            "csrf_token": security.csrf_token(request),
        },
    )


@app.post(
    "/predict",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access), Depends(require_csrf_form)],
)
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
                "csrf_token": security.csrf_token(request),
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
                "error": (
                    f"Request failed. Reference: {request.state.request_id}"
                    if security.settings.production
                    else str(exc)
                ),
                "runtime": "MOCK" if pipeline.llm.use_mock else "LIVE",
                "model": pipeline.llm.model,
                "diagnostics": build_diagnostics(),
                "csrf_token": security.csrf_token(request),
            },
            status_code=400,
        )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/diagnostics", dependencies=[Depends(require_operator_access)])
def diagnostics() -> dict:
    return build_diagnostics()


@app.get(
    "/api/metrics",
    response_model=OperationalMetrics,
    dependencies=[Depends(require_operator_access)],
)
def api_metrics() -> OperationalMetrics:
    return build_operational_metrics()


@app.get(
    "/review",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access)],
)
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
            "csrf_token": security.csrf_token(request),
        },
    )


@app.post(
    "/review/{task_id}/decision",
    dependencies=[Depends(require_admin_access), Depends(require_csrf_form)],
)
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


@app.post(
    "/api/listings/analyze",
    response_model=CatalogQualityDecision,
    dependencies=[Depends(require_api_access)],
)
def analyze_listing(listing: ListingInput) -> CatalogQualityDecision:
    return current_catalog_quality_graph().analyze(listing)


@app.get(
    "/api/review-queue",
    response_model=list[ReviewQueueItem],
    dependencies=[Depends(require_operator_access)],
)
def list_review_queue(status: str = "pending", limit: int = 100) -> list[ReviewQueueItem]:
    try:
        return review_store.list_review_tasks(status=status or None, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/api/workflow-runs",
    response_model=list[WorkflowRun],
    dependencies=[Depends(require_operator_access)],
)
def list_workflow_runs(status: str = "", limit: int = 100) -> list[WorkflowRun]:
    try:
        return review_store.list_workflow_runs(
            status=status or None,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/api/workflow-runs/{workflow_run_id}",
    response_model=WorkflowRunDetail,
    dependencies=[Depends(require_operator_access)],
)
def get_workflow_run(workflow_run_id: str) -> WorkflowRunDetail:
    workflow = review_store.get_workflow_run_detail(workflow_run_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"workflow run not found: {workflow_run_id}",
        )
    return workflow


@app.get(
    "/api/workflow-runs/{workflow_run_id}/agents",
    response_model=list[AgentRun],
    dependencies=[Depends(require_operator_access)],
)
def list_workflow_agent_runs(workflow_run_id: str) -> list[AgentRun]:
    workflow = review_store.get_workflow_run(workflow_run_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"workflow run not found: {workflow_run_id}",
        )
    return review_store.list_agent_runs(workflow_run_id)


@app.get(
    "/api/review-queue/{task_id}",
    response_model=ReviewTask,
    dependencies=[Depends(require_operator_access)],
)
def get_review_task(task_id: str) -> ReviewTask:
    task = review_store.get_review_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"review task not found: {task_id}")
    return task


@app.post(
    "/api/review-queue/{task_id}/decision",
    response_model=ReviewTask,
    dependencies=[Depends(require_api_access)],
)
def record_review_task_decision(task_id: str, decision: ReviewDecision) -> ReviewTask:
    try:
        return review_store.record_review_decision(task_id, decision)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/dashboard",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access)],
)
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
            "csrf_token": security.csrf_token(request),
        },
    )


@app.get(
    "/artifacts/results.json",
    dependencies=[Depends(require_operator_access)],
)
def artifact_results_json() -> FileResponse:
    if not RESULTS_JSON_PATH.exists():
        raise HTTPException(status_code=404, detail=f"{RESULTS_JSON_PATH} not found")
    return FileResponse(RESULTS_JSON_PATH, media_type="application/json", filename="results.json")


@app.get(
    "/artifacts/results.md",
    dependencies=[Depends(require_operator_access)],
)
def artifact_results_md() -> FileResponse:
    if not RESULTS_MD_PATH.exists():
        raise HTTPException(status_code=404, detail=f"{RESULTS_MD_PATH} not found")
    return FileResponse(RESULTS_MD_PATH, media_type="text/markdown", filename="results.md")
