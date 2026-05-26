import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from reliable_genai.models import ProductInput
from reliable_genai.pipeline import ReliabilityPipeline
from reliable_genai.review_graph import ReviewGraphRunner

load_dotenv()

app = FastAPI(title="Reliable GenAI Demo")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

pipeline = ReliabilityPipeline()
review_graph = ReviewGraphRunner(pipeline)
RESULTS_JSON_PATH = Path("reports/results.json")
RESULTS_MD_PATH = Path("reports/results.md")


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
    }


def load_results_artifact(path: Path = RESULTS_JSON_PATH) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"{path} not found"
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as exc:
        return None, f"failed to parse {path}: {exc}"


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
