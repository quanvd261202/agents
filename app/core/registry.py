"""Generic in-memory registry shared by components, tokens, layouts, recipes, animations."""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterable, Iterator
from typing import Protocol

from app.core.exceptions import ValidationError


class HasId(Protocol):
    @property
    def id(self) -> str: ...


class DuplicateIdError(ValidationError): ...


class BaseRegistry[T: HasId]:
    not_found_error: type[ValidationError] = ValidationError
    kind: str = "item"

    def __init__(self, items: Iterable[T] = ()) -> None:
        self._items: dict[str, T] = {}
        for item in items:
            self.register(item)

    def register(self, item: T) -> None:
        if item.id in self._items:
            raise DuplicateIdError(f"duplicate {self.kind} id: {item.id}", target=item.id)
        self._items[item.id] = item

    def get(self, item_id: str) -> T:
        try:
            return self._items[item_id]
        except KeyError:
            raise self.not_found_error(f"unknown {self.kind}: {item_id}", target=item_id) from None

    def exists(self, item_id: str) -> bool:
        return item_id in self._items

    def list(self) -> builtins.list[T]:
        return builtins.list(self._items.values())

    def ids(self) -> builtins.list[str]:
        return builtins.list(self._items)

    def filter(self, predicate: Callable[[T], bool]) -> builtins.list[T]:
        return [i for i in self._items.values() if predicate(i)]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, item_id: object) -> bool:
        return item_id in self._items
