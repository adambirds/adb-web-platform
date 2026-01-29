from ninja import Schema


class Pagination(Schema):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    next_page: int | None = None
    previous_page: int | None = None
