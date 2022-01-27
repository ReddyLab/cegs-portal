from abc import abstractmethod
from typing import Protocol, TypeVar

T = TypeVar("T")


class Paginateable(Protocol[T]):
    @abstractmethod
    def get_page(self, number) -> "Pageable[T]":
        raise NotImplementedError

    @abstractmethod
    def page(self, number) -> "Pageable[T]":
        raise NotImplementedError

    @property
    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def num_pages(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def page_range(self) -> range:
        raise NotImplementedError


class Pageable(Protocol[T]):
    object_list: list[T]
    number: int
    paginator: Paginateable[T]

    @abstractmethod
    def __getitem__(self, index) -> T:
        raise NotImplementedError

    @abstractmethod
    def has_next(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_previous(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_other_pages(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def next_page_number(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def previous_page_number(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def start_index(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def end_index(self) -> int:
        raise NotImplementedError
