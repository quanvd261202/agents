from __future__ import annotations

from app.core.config import Settings
from app.db.session import build_session_factory, prepare
from app.learning.service import LearningService
from app.learning.store import InMemoryLessonRepository, PgLessonRepository
from app.recipes import default_recipe_registry
from app.retrieval.factory import build_embeddings
from app.services.repositories import LessonRepository


async def build_lesson_repository(settings: Settings) -> LessonRepository:
    """Postgres when `persistence` asks for it and the database answers; otherwise in-memory."""
    embeddings = build_embeddings(settings)
    if settings.persistence == "postgres":
        repo = PgLessonRepository(build_session_factory(settings.database_url), embeddings)
        if await prepare("lessons", repo.create_schema()):
            return repo
    return InMemoryLessonRepository(embeddings)


async def build_learning_service(settings: Settings) -> LearningService:
    return LearningService(await build_lesson_repository(settings), default_recipe_registry())
