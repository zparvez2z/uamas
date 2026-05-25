import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
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


def build_diagnostics() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    classifier_diagnostics = pipeline.classifier.diagnostics()
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
        "classifier_runtime": classifier_diagnostics["runtime"],
        "classifier_ready": classifier_diagnostics["ready"],
        "classifier_reason": classifier_diagnostics["reason"],
        "classifier_artifact_path": classifier_diagnostics["artifact_path"],
        "classifier_model_type": classifier_diagnostics.get("model_type"),
        "classifier_artifact_load_attempted": classifier_diagnostics.get("artifact_load_attempted", False),
        "classifier_artifact_load_status": classifier_diagnostics.get("artifact_load_status", "not_attempted"),
        "classifier_artifact_rejection_reason": classifier_diagnostics.get("artifact_rejection_reason"),
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
        "review_graph_trigger_rate": review_diagnostics.get("review_graph_trigger_rate"),
        "review_graph_second_pass_rate": review_diagnostics.get("review_graph_second_pass_rate"),
        "review_graph_cache_hit_rate": review_diagnostics.get("review_graph_cache_hit_rate"),
        "review_graph_cached_step_count": review_diagnostics.get("review_graph_cached_step_count"),
    }


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
