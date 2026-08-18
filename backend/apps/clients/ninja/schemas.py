from datetime import date
from decimal import Decimal

from ninja import Schema


class ClientSummaryOut(Schema):
    id: int
    name: str
    company: str
    email: str
    status: str
    contact_count: int
    project_count: int


class ClientContactOut(Schema):
    id: int
    name: str
    email: str
    phone: str
    role: str
    is_active: bool
    is_primary: bool
    is_billing: bool
    is_technical: bool


class ClientProjectOut(Schema):
    id: int
    name: str
    status: str
    start_date: date
    end_date: date | None
    budget: Decimal | None


class ClientDetailOut(Schema):
    id: int
    name: str
    company: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    status: str
    notes: str
    contacts: list[ClientContactOut]
    projects: list[ClientProjectOut]


class ProjectSummaryOut(Schema):
    id: int
    name: str
    status: str
    ownership_type: str
    client_id: int | None
    client_name: str | None
    start_date: date
    end_date: date | None
    budget: Decimal | None


class TimeEntrySummaryOut(Schema):
    id: int
    date: date
    duration_hours: Decimal
    description: str
    billable: bool
    ownership_type: str
    client_name: str | None
    project_name: str | None
    user_name: str | None
