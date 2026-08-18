from datetime import datetime

from ninja import Schema


class LeadSummaryOut(Schema):
    id: int
    name: str
    company: str
    email: str
    status: str
    source: str
    brand: str
    created_at: datetime
