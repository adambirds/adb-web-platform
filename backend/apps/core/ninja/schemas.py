from ninja import Schema


class BrandOut(Schema):
    id: int
    name: str
    slug: str
    domain: str
    is_active: bool
