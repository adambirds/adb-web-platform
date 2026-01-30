from adbsoftwaresolutions.ninja.schema import Pagination


def serialize_pagination(
    page: int, page_size: int, total_pages: int, total_items: int
) -> Pagination:
    return Pagination(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next_page=page < total_pages,
        has_previous_page=page > 1,
        next_page=page + 1 if page < total_pages else None,
        previous_page=page - 1 if page > 1 else None,
    )
