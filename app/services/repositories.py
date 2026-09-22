from typing import Protocol

from app.models import Lesson


class LessonRepository(Protocol):
    async def search(self, query: str, scope: dict[str, str], limit: int) -> list[Lesson]: ...
    async def upsert(self, lesson: Lesson) -> None: ...


class RunRepository(Protocol):
    async def save_stage(self, run_id: str, stage: str, payload: dict[str, object]) -> None: ...
