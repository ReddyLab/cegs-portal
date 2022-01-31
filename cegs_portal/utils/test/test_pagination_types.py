import pytest

from cegs_portal.utils.pagination_types import MockPaginator

mockpaginators: list[MockPaginator[int]] = [
    MockPaginator([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 1),
    MockPaginator([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 2),
    MockPaginator([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 3),
    MockPaginator([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 4),
    MockPaginator([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 20),
]


@pytest.mark.parametrize(
    "page, objects",
    [
        (mockpaginators[0].page(4), [3]),
        (mockpaginators[1].page(4), [6, 7]),
        (mockpaginators[2].page(4), [9, 10, 11]),
        (mockpaginators[3].page(4), [12, 13]),
    ],
)
def test_mockpage_objects(page, objects):
    assert page.object_list == objects


@pytest.mark.parametrize(
    "page, index, item",
    [
        (mockpaginators[0].get_page(4), 0, 3),
        (mockpaginators[1].get_page(4), 0, 6),
        (mockpaginators[2].get_page(4), 1, 10),
        (mockpaginators[3].get_page(4), 1, 13),
    ],
)
def test_mockpage_get_item(page, index, item):
    assert page[index] == item


@pytest.mark.parametrize(
    "page, has_next",
    [
        (mockpaginators[0].get_page(4), True),
        (mockpaginators[1].get_page(4), True),
        (mockpaginators[2].get_page(4), True),
        (mockpaginators[3].get_page(4), False),
    ],
)
def test_mockpage_has_next(page, has_next):
    assert page.has_next() == has_next


@pytest.mark.parametrize(
    "page, has_previous",
    [
        (mockpaginators[0].get_page(1), False),
        (mockpaginators[1].get_page(1), False),
        (mockpaginators[2].get_page(2), True),
        (mockpaginators[3].get_page(2), True),
    ],
)
def test_mockpage_has_previous(page, has_previous):
    assert page.has_previous() == has_previous


@pytest.mark.parametrize(
    "page, has_other_pages",
    [
        (mockpaginators[0].get_page(1), True),
        (mockpaginators[1].get_page(1), True),
        (mockpaginators[2].get_page(2), True),
        (mockpaginators[3].get_page(2), True),
        (mockpaginators[4].get_page(1), False),
    ],
)
def test_mockpage_has_other_pages(page, has_other_pages):
    assert page.has_other_pages() == has_other_pages


@pytest.mark.parametrize(
    "page, next_page_number",
    [
        (mockpaginators[0].get_page(1), 2),
        (mockpaginators[1].get_page(1), 2),
        (mockpaginators[2].get_page(2), 3),
        (mockpaginators[3].get_page(2), 3),
    ],
)
def test_mockpage_next_page_number(page, next_page_number):
    assert page.next_page_number() == next_page_number


@pytest.mark.parametrize(
    "page, previous_page_number",
    [
        (mockpaginators[0].get_page(1), 0),
        (mockpaginators[1].get_page(1), 0),
        (mockpaginators[2].get_page(2), 1),
        (mockpaginators[3].get_page(2), 1),
    ],
)
def test_mockpage_previous_page_number(page, previous_page_number):
    assert page.previous_page_number() == previous_page_number


@pytest.mark.parametrize(
    "page, start_index",
    [
        (mockpaginators[0].get_page(4), 4),
        (mockpaginators[1].get_page(4), 7),
        (mockpaginators[2].get_page(4), 10),
        (mockpaginators[3].get_page(4), 13),
    ],
)
def test_mockpage_start_index(page, start_index):
    assert page.start_index() == start_index


@pytest.mark.parametrize(
    "paginator, page, objects",
    [
        (mockpaginators[0], 4, [3]),
        (mockpaginators[1], 4, [6, 7]),
        (mockpaginators[2], 4, [9, 10, 11]),
        (mockpaginators[3], 4, [12, 13]),
    ],
)
def test_mockpaginator_pageobjects(paginator, page, objects):
    assert paginator.page(page).object_list == objects


@pytest.mark.parametrize(
    "paginator, count",
    [
        (mockpaginators[0], 14),
        (mockpaginators[1], 14),
        (mockpaginators[2], 14),
        (mockpaginators[3], 14),
    ],
)
def test_mockpaginator_count(paginator, count):
    assert paginator.count == count


@pytest.mark.parametrize(
    "paginator, num_pages",
    [
        (mockpaginators[0], 14),
        (mockpaginators[1], 7),
        (mockpaginators[2], 5),
        (mockpaginators[3], 4),
    ],
)
def test_mockpaginator_num_pages(paginator, num_pages):
    assert paginator.num_pages == num_pages


@pytest.mark.parametrize(
    "paginator, page_range",
    [
        (mockpaginators[0], range(1, 15)),
        (mockpaginators[1], range(1, 8)),
        (mockpaginators[2], range(1, 6)),
        (mockpaginators[3], range(1, 5)),
    ],
)
def test_mockpaginator_page_range(paginator, page_range):
    assert paginator.page_range == page_range
