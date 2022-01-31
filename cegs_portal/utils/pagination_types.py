from abc import abstractmethod
from collections.abc import Iterable, Iterator
from math import ceil
from typing import Protocol, TypeVar

T = TypeVar("T")


class Paginateable(Protocol[T]):
    per_page: int

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


class Pageable(Protocol[T], Iterable[T]):
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


class MockPaginator(Paginateable[T]):
    def __init__(self, object_list, per_page):
        self.object_list = object_list
        self.per_page = per_page

    def get_page(self, number) -> Pageable[T]:
        return self.page(number)

    def page(self, number) -> Pageable[T]:
        start = (number - 1) * self.per_page
        last_index = len(self.object_list) - 1
        if last_index < start:
            object_list = []
        else:
            end = start + self.per_page
            if last_index < end:
                end = last_index + 1
            object_list = self.object_list[start:end]
        return MockPage(object_list, self, number)

    @property
    def count(self) -> int:
        return len(self.object_list)

    @property
    def num_pages(self) -> int:
        return ceil(len(self.object_list) / self.per_page)

    @property
    def page_range(self) -> range:
        return range(1, self.num_pages + 1)


class MockPage(Pageable[T]):
    def __init__(self, object_list, paginator, number):
        self.object_list = object_list
        self.paginator = paginator
        self.number = number

    def __getitem__(self, index) -> T:
        return self.object_list[index]

    def has_next(self) -> bool:
        return self.number < self.paginator.num_pages

    def has_previous(self) -> bool:
        return self.number > 1

    def has_other_pages(self) -> bool:
        return self.has_previous() or self.has_next()

    def next_page_number(self) -> int:
        return self.number + 1

    def previous_page_number(self) -> int:
        return self.number - 1

    def start_index(self):
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """
        Return the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page

    def __iter__(self) -> Iterator[T]:
        for o in self.object_list:
            yield o
