from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int

    @computed_field
    @property
    def pages(self) -> int:
        return ceil(self.total / self.per_page) if self.total > 0 else 1
