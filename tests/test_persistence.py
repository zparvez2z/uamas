from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from reliable_genai.models import (
    AgentTrace,
    ListingInput,
    PredictionResponse,
    ProductAttributes,
    ReliabilityMeta,
    ReviewDecision,
)
from reliable_genai.persistence import SQLiteReviewStore, resolve_db_path
from reliable_genai.workflow_history import WorkflowRecorder


def _prediction() -> PredictionResponse:
    return PredictionResponse(
        category_set=["Shoes"],
        attributes=ProductAttributes(brand="Acme", color="black", material="mesh", size="42"),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=1,
            confidence=0.91,
            abstained=False,
            reason=None,
            policy_action="set_output",
            llm_runtime="MOCK",
            llm_model="mock-model",
            classifier_runtime="ARTIFACT",
            classifier_reason=None,
            classifier_artifact_path="artifacts/classifier.joblib",
            classifier_model_type="embedding",
            coverage_threshold=0.9,
        ),
    )


def test_resolve_db_path_uses_env_override(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "custom.db"
    monkeypatch.setenv("UAMAS_DB_PATH", str(path))

    assert resolve_db_path() == path


def test_store_creates_listing_prediction_and_review_task(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(
        ListingInput(title="ambiguous running shoe", description="could be apparel or sports gear")
    )
    prediction_id = store.create_prediction(listing_id, _prediction())

    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=prediction_id,
        reason="low_confidence_large_set",
        risk_level="high",
    )

    assert task.id.startswith("rev_")
    assert task.listing_id == listing_id
    assert task.prediction_id == prediction_id
    assert task.status == "pending"
    assert task.reason == "low_confidence_large_set"
    assert task.risk_level == "high"

    fetched = store.get_review_task(task.id)
    assert fetched == task

    pending = store.list_review_tasks(status="pending")
    assert len(pending) == 1
    assert pending[0].title == "ambiguous running shoe"
    assert pending[0].description == "could be apparel or sports gear"


def test_store_records_review_decision(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(ListingInput(title="dress shoe", description="formal leather"))
    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=None,
        reason="abstained",
    )

    updated = store.record_review_decision(
        task.id,
        ReviewDecision(
            action="correct",
            corrected_category="Shoes",
            corrected_attributes={"material": "leather"},
            notes="Correct category after review.",
        ),
    )

    assert updated.status == "corrected"
    assert updated.corrected_category == "Shoes"
    assert updated.corrected_attributes == {"material": "leather"}
    assert updated.notes == "Correct category after review."
    assert store.list_review_tasks(status="pending") == []
    assert len(store.list_review_tasks(status="corrected")) == 1


def test_store_diagnostics_counts_review_tasks(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(ListingInput(title="item", description="desc"))
    task = store.create_review_task(listing_id=listing_id, prediction_id=None, reason="abstained")

    diagnostics = store.diagnostics()
    assert diagnostics["available"] is True
    assert diagnostics["listing_count"] == 1
    assert diagnostics["review_task_count"] == 1
    assert diagnostics["pending_review_task_count"] == 1

    store.record_review_decision(task.id, ReviewDecision(action="approve"))
    diagnostics = store.diagnostics()
    assert diagnostics["review_task_count"] == 1
    assert diagnostics["pending_review_task_count"] == 0


def test_store_metrics_counts_statuses_reasons_and_rates(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    auto_listing_id = store.create_listing(ListingInput(title="accepted shoe", description="clear shoe"))
    store.create_prediction(auto_listing_id, _prediction())

    pending_listing_id = store.create_listing(ListingInput(title="pending item", description="unclear"))
    pending_prediction_id = store.create_prediction(pending_listing_id, _prediction())
    store.create_review_task(
        listing_id=pending_listing_id,
        prediction_id=pending_prediction_id,
        reason="low_confidence",
    )

    corrected_listing_id = store.create_listing(ListingInput(title="corrected item", description="unclear"))
    corrected_prediction_id = store.create_prediction(corrected_listing_id, _prediction())
    corrected_task = store.create_review_task(
        listing_id=corrected_listing_id,
        prediction_id=corrected_prediction_id,
        reason="low_semantic_consistency",
    )
    store.record_review_decision(corrected_task.id, ReviewDecision(action="correct", corrected_category="Sports"))

    metrics = store.metrics()

    assert metrics["available"] is True
    assert metrics["listing_count"] == 3
    assert metrics["prediction_count"] == 3
    assert metrics["review_task_count"] == 2
    assert metrics["auto_accept_count"] == 1
    assert metrics["needs_human_review_count"] == 2
    assert metrics["pending_review_task_count"] == 1
    assert metrics["corrected_review_task_count"] == 1
    assert metrics["review_status_counts"] == {"corrected": 1, "pending": 1}
    assert metrics["review_reason_counts"] == {"low_confidence": 1, "low_semantic_consistency": 1}
    assert metrics["auto_accept_rate"] == 0.333
    assert metrics["human_review_rate"] == 0.667
    assert metrics["correction_rate"] == 0.5


def test_store_rejects_invalid_limit(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")

    with pytest.raises(ValueError, match="limit must be positive"):
        store.list_review_tasks(limit=0)


def test_store_raises_for_missing_review_task(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")

    with pytest.raises(KeyError, match="review task not found"):
        store.record_review_decision("rev_missing", ReviewDecision(action="reject"))


def test_store_does_not_overwrite_resolved_review_decision(
    tmp_path: Path,
) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(
        ListingInput(title="item", description="description")
    )
    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=None,
        reason="abstained",
    )
    approved = store.record_review_decision(
        task.id,
        ReviewDecision(action="approve"),
    )

    with pytest.raises(ValueError, match="already resolved"):
        store.record_review_decision(
            task.id,
            ReviewDecision(
                action="correct",
                corrected_category="Sports",
            ),
        )

    assert store.get_review_task(task.id) == approved


def test_store_rejects_ambiguous_prediction_approval(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(
        ListingInput(title="ambiguous", description="description")
    )
    prediction = _prediction().model_copy(deep=True)
    prediction.category_set = ["Shoes", "Sports"]
    prediction.reliability.set_size = 2
    prediction_id = store.create_prediction(listing_id, prediction)
    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=prediction_id,
        reason="large_set",
    )

    with pytest.raises(ValueError, match="single predicted category"):
        store.record_review_decision(
            task.id,
            ReviewDecision(action="approve"),
        )

    assert store.get_review_task(task.id).status == "pending"


def test_store_rejects_unknown_corrected_category(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(
        ListingInput(title="item", description="description")
    )
    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=None,
        reason="review",
    )

    with pytest.raises(ValueError, match="corrected category must be one of"):
        store.record_review_decision(
            task.id,
            ReviewDecision(
                action="correct",
                corrected_category="Unsupported",
            ),
        )

    assert store.get_review_task(task.id).status == "pending"


def test_store_persists_completed_workflow_and_agent_history(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    workflow = store.start_workflow_run(
        ListingInput(external_id="seller-1", title="running shoe", description="black mesh"),
        graph_backend="langgraph",
    )
    agent_run = store.start_agent_run(
        workflow.id,
        agent_name="classifier_agent",
        input_summary={"listing_id": workflow.listing_id},
    )
    store.complete_agent_run(
        agent_run.id,
        status="completed",
        output={"category_set": ["Shoes"], "confidence": 0.91},
        reason=None,
        duration_ms=12.5,
    )
    prediction_id = store.create_prediction_for_workflow(
        workflow.id,
        listing_id=workflow.listing_id,
        prediction=_prediction(),
    )
    task = store.create_review_task_for_workflow(
        workflow.id,
        listing_id=workflow.listing_id,
        prediction_id=prediction_id,
        reason="low_confidence",
        risk_level="high",
    )
    completed = store.complete_workflow_run(
        workflow.id,
        decision="needs_human_review",
        risk_level="high",
        duration_ms=25.0,
    )

    assert completed.status == "completed"
    assert completed.prediction_id == prediction_id
    assert completed.review_task_id == task.id
    detail = store.get_workflow_run_detail(workflow.id)
    assert detail is not None
    assert detail.listing_id == workflow.listing_id
    assert len(detail.agent_runs) == 1
    assert detail.agent_runs[0].agent_name == "classifier_agent"
    assert detail.agent_runs[0].status == "completed"
    assert detail.agent_runs[0].output["category_set"] == ["Shoes"]


def test_workflow_recorder_persists_degraded_and_failed_agent_runs(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    workflow = store.start_workflow_run(
        ListingInput(title="item", description="description"),
        graph_backend="sequential",
    )
    recorder = WorkflowRecorder(store)

    result, trace = recorder.run(
        workflow_run_id=workflow.id,
        agent_name="semantic_critic_agent",
        operation=lambda: "degraded-result",
        trace_builder=lambda _: AgentTrace(
            agent="semantic_critic_agent",
            status="degraded",
            output={"score": None},
            reason="embedding_client_unavailable",
        ),
    )

    assert result == "degraded-result"
    assert trace.status == "degraded"

    def fail_operation() -> str:
        raise RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        recorder.run(
            workflow_run_id=workflow.id,
            agent_name="attribute_extraction_agent",
            operation=fail_operation,
            trace_builder=lambda _: AgentTrace(agent="attribute_extraction_agent", status="ok"),
        )

    runs = store.list_agent_runs(workflow.id)
    assert [run.status for run in runs] == ["degraded", "failed"]
    assert runs[1].error_type == "RuntimeError"
    assert runs[1].error_message == "provider failed"


def test_failed_workflow_is_not_counted_as_auto_accept(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    workflow = store.start_workflow_run(
        ListingInput(title="failed item", description="description"),
        graph_backend="langgraph",
    )
    store.fail_workflow_run(
        workflow.id,
        error_type="RuntimeError",
        error_message="x" * 2000,
        duration_ms=5.0,
    )

    metrics = store.metrics()
    failed = store.get_workflow_run(workflow.id)

    assert failed is not None
    assert failed.status == "failed"
    assert len(failed.error_message) == 1000
    assert metrics["listing_count"] == 1
    assert metrics["workflow_run_count"] == 1
    assert metrics["failed_workflow_run_count"] == 1
    assert metrics["auto_accept_count"] == 0
    assert metrics["needs_human_review_count"] == 0


def test_workflow_history_redacts_configured_credentials(monkeypatch, tmp_path: Path) -> None:
    secret = "github_pat_secret-value"
    monkeypatch.setenv("GITHUB_TOKEN", secret)
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    workflow = store.start_workflow_run(
        ListingInput(title="failed item", description="description"),
        graph_backend="langgraph",
    )
    store.fail_workflow_run(
        workflow.id,
        error_type="RuntimeError",
        error_message=f"provider rejected token {secret}",
        duration_ms=5.0,
    )

    failed = store.get_workflow_run(workflow.id)
    assert failed is not None
    assert secret not in failed.error_message
    assert "[REDACTED]" in failed.error_message


def test_parallel_agent_history_writes_do_not_lock_database(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    workflow = store.start_workflow_run(
        ListingInput(title="parallel item", description="description"),
        graph_backend="langgraph",
    )

    def write_agent(agent_name: str) -> None:
        run = store.start_agent_run(workflow.id, agent_name=agent_name)
        store.complete_agent_run(
            run.id,
            status="completed",
            output={"agent": agent_name},
            reason=None,
            duration_ms=1.0,
        )

    names = [f"agent_{index}" for index in range(8)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(write_agent, names))

    runs = store.list_agent_runs(workflow.id)
    assert len(runs) == len(names)
    assert {run.agent_name for run in runs} == set(names)
    assert all(run.status == "completed" for run in runs)


def test_store_lists_and_filters_workflow_runs(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    completed = store.start_workflow_run(
        ListingInput(title="completed", description="description"),
        graph_backend="langgraph",
    )
    store.complete_workflow_run(
        completed.id,
        decision="auto_accept",
        risk_level="low",
        duration_ms=10.0,
    )
    failed = store.start_workflow_run(
        ListingInput(title="failed", description="description"),
        graph_backend="sequential",
    )
    store.fail_workflow_run(
        failed.id,
        error_type="RuntimeError",
        error_message="failed",
        duration_ms=4.0,
    )

    assert len(store.list_workflow_runs()) == 2
    assert [run.id for run in store.list_workflow_runs(status="completed")] == [completed.id]
    assert [run.id for run in store.list_workflow_runs(status="failed")] == [failed.id]
    with pytest.raises(ValueError, match="invalid workflow status"):
        store.list_workflow_runs(status="unknown")
