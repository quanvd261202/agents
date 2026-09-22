import pytest

from app.core.exceptions import ConfigurationError
from app.models.direction import DesignDirection
from app.models.requirements import ClarifiedRequirements
from app.retrieval import (
    HashingEmbeddingProvider,
    InMemoryRetrievalRepository,
    RetrievalBudget,
    RetrievalFilters,
    RetrievalIndex,
    RetrievalKind,
    RetrievalService,
    build_documents,
    build_embedding_provider,
)
from app.retrieval.repository import cosine
from app.retrieval.service import estimate_tokens

ECOM = ClarifiedRequirements(
    product="running shoe store",
    domain="ecommerce",
    target_audience="runners",
    primary_goal="sell shoes",
    key_features=["product browsing", "reviews", "checkout"],
)
ECOM_DIRECTION = DesignDirection(
    visual_style="premium_modern",
    theme="premium_light",
    typography="modern_sans",
    radius="large",
    layout_strategy="editorial_grid",
    animation="subtle",
    recipe="ecommerce_product",
)
SAAS = ClarifiedRequirements(
    product="analytics dashboard",
    domain="saas",
    target_audience="ops teams",
    primary_goal="monitor metrics",
    key_features=["charts", "statistics", "activity"],
)
SAAS_DIRECTION = DesignDirection(
    visual_style="premium_dark",
    theme="premium_dark",
    typography="geometric",
    radius="large",
    layout_strategy="bento",
    animation="subtle",
    recipe="dashboard",
)


@pytest.fixture
async def service():
    embeddings = HashingEmbeddingProvider(dimensions=512)
    repo = InMemoryRetrievalRepository()
    await RetrievalIndex(embeddings, repo).rebuild()
    return RetrievalService(embeddings, repo)


def test_documents_cover_every_registry():
    docs = build_documents()
    kinds = {d.kind for d in docs}
    assert kinds == {RetrievalKind.component, RetrievalKind.layout, RetrievalKind.recipe}
    assert len({d.key for d in docs}) == len(docs)
    assert all(d.summary and d.text for d in docs)


async def test_index_is_written_once(service):
    assert await service._repository.count() == len(build_documents())


def test_hashing_embeddings_are_deterministic_and_normalised():
    a = HashingEmbeddingProvider(64)
    b = HashingEmbeddingProvider(64)
    import asyncio

    v1 = asyncio.run(a.embed_query("premium saas analytics dashboard"))
    v2 = asyncio.run(b.embed_query("premium saas analytics dashboard"))
    assert v1 == v2
    assert cosine(v1, v2) == pytest.approx(1.0)
    assert len(v1) == 64


async def test_semantic_search_finds_relevant_components(service):
    hits = await service.search(
        "premium saas analytics dashboard statistics charts",
        RetrievalFilters(kinds=[RetrievalKind.component]),
        limit=8,
    )
    ids = {h.document.id for h in hits}
    assert ids & {"stats", "chart_panel", "activity_feed", "data_table"}
    assert all(hits[i].score >= hits[i + 1].score for i in range(len(hits) - 1))


async def test_domain_filter_excludes_other_domains(service):
    hits = await service.search(
        "product card grid",
        RetrievalFilters(kinds=[RetrievalKind.component], domain="saas"),
        limit=20,
    )
    ids = {h.document.id for h in hits}
    assert "product_card" not in ids and "product_detail" not in ids
    assert "hero" in ids  # domain-agnostic components stay available


async def test_capability_and_category_filters(service):
    any_caps = await service.search("trust", RetrievalFilters(any_capabilities=["trust"]), limit=20)
    assert {h.document.id for h in any_caps} >= {"social_proof", "trust_signals", "reviews"}
    commerce = await service.search("anything", RetrievalFilters(category="commerce"), limit=20)
    assert all(h.document.category == "commerce" for h in commerce)
    both = await service.search(
        "grid", RetrievalFilters(all_capabilities=["commerce", "responsive"]), limit=20
    )
    assert {h.document.id for h in both} <= {"product_card", "product_grid"}


async def test_exclude_ids(service):
    hits = await service.search("hero", RetrievalFilters(exclude_ids=["hero"]), limit=10)
    assert "hero" not in {h.document.id for h in hits}


async def test_retrieve_builds_compact_context_per_domain(service):
    ecom = await service.retrieve(ECOM, ECOM_DIRECTION)
    saas = await service.retrieve(SAAS, SAAS_DIRECTION)

    assert ecom.recipes and saas.recipes
    assert all("product" not in line for line in saas.components)
    assert ecom.components and ecom.layouts
    # a compact context, not the catalog
    assert len(ecom.components) < len(build_documents())
    assert ecom.estimated_tokens <= RetrievalBudget().max_tokens


async def test_budget_trims_and_always_keeps_a_recipe(service):
    tight = RetrievalService(
        service._embeddings, service._repository, RetrievalBudget(max_tokens=60)
    )
    ctx = await tight.retrieve(ECOM, ECOM_DIRECTION)
    assert ctx.estimated_tokens <= 60 or len(ctx.components) == 1
    assert ctx.recipes
    assert estimate_tokens(ctx.components) < estimate_tokens(
        (await service.retrieve(ECOM, ECOM_DIRECTION)).components
    )


async def test_lessons_are_capped(service):
    ctx = await service.retrieve(ECOM, ECOM_DIRECTION, lessons=[f"lesson {i}" for i in range(20)])
    assert len(ctx.lessons) <= RetrievalBudget().max_lessons


async def test_context_exposes_ids_for_validation(service):
    ctx = await service.retrieve(ECOM, ECOM_DIRECTION)
    from app.catalog import default_component_registry

    reg = default_component_registry()
    assert all(reg.exists(cid) for cid in ctx.component_ids())


def test_provider_factory_and_unknown_provider():
    assert build_embedding_provider("hashing", dimensions=128).dimensions == 128
    with pytest.raises(ConfigurationError):
        build_embedding_provider("word2vec")


def test_openai_provider_is_constructible_without_network(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = build_embedding_provider("openai", "text-embedding-3-small", 1536)
    assert provider.dimensions == 1536
    assert provider.name == "text-embedding-3-small-1536"
