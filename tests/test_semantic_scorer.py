from reliable_genai.models import ProductInput
from reliable_genai.semantic_scorer import SemanticConsistencyScorer


class FakeEmbedResult:
    def __init__(self, vectors):
        self.data = [{"embedding": vector} for vector in vectors]


class FakeEmbeddingsClient:
    def __init__(self, vector_map, should_fail=False):
        self.vector_map = vector_map
        self.should_fail = should_fail
        self.calls = 0

    def embed(self, *, input, model):
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("embedding backend unavailable")
        return FakeEmbedResult([self.vector_map[text] for text in input])


def test_semantic_scorer_returns_bounded_score() -> None:
    labels = ["Shoes", "Clothing"]
    scorer = SemanticConsistencyScorer(
        labels,
        enabled=True,
        endpoint="https://models.github.ai/inference",
        api_key="test-token",
        model="openai/text-embedding-3-small",
    )

    query_text = "nike running shoe breathable mesh"
    vector_map = {
        query_text: [1.0, 0.0],
        scorer.prototypes["Shoes"]: [0.9, 0.1],
        scorer.prototypes["Clothing"]: [0.0, 1.0],
    }
    scorer._client = FakeEmbeddingsClient(vector_map)
    item = ProductInput(title="nike running shoe", description="breathable mesh")

    result = scorer.score(item, candidate_labels=["Shoes", "Clothing"])

    assert result.status == "ok"
    assert result.reason is None
    assert result.score is not None
    assert 0.0 <= result.score <= 1.0
    assert scorer.diagnostics()["ok_requests"] == 1


def test_semantic_scorer_degrades_gracefully_on_embedding_failure() -> None:
    labels = ["Shoes", "Clothing"]
    scorer = SemanticConsistencyScorer(
        labels,
        enabled=True,
        endpoint="https://models.github.ai/inference",
        api_key="test-token",
        model="openai/text-embedding-3-small",
    )
    scorer._client = FakeEmbeddingsClient({}, should_fail=True)

    result = scorer.score(ProductInput(title="nike shoe", description="black size 42"))

    assert result.status == "degraded"
    assert result.score is None
    assert result.reason is not None
    assert scorer.diagnostics()["degraded_requests"] == 1


def test_semantic_scorer_disabled_state() -> None:
    scorer = SemanticConsistencyScorer(
        ["Shoes"],
        enabled=False,
    )

    result = scorer.score(ProductInput(title="nike shoe", description="black size 42"))

    assert result.status == "disabled"
    assert result.score is None
    assert result.reason == "semantic_scorer_disabled"
