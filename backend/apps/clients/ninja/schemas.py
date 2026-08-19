import datetime
import decimal
import typing

from ninja import Schema

ClientStatus = typing.Literal["active", "inactive", "archived"]


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


class ClientContactIn(Schema):
    name: str
    email: str
    phone: str = ""
    role: str = ""
    is_active: bool = True
    is_primary: bool = False
    is_billing: bool = False
    is_technical: bool = False


class ClientProjectOut(Schema):
    id: int
    name: str
    status: str
    start_date: datetime.date
    end_date: datetime.date | None
    budget: decimal.Decimal | None


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


class ClientIn(Schema):
    name: str
    company: str = ""
    email: str
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""
    status: ClientStatus = "active"
    notes: str = ""


class ProjectSummaryOut(Schema):
    id: int
    name: str
    status: str
    ownership_type: str
    client_id: int | None
    client_name: str | None
    start_date: datetime.date
    end_date: datetime.date | None
    budget: decimal.Decimal | None


class TimeEntrySummaryOut(Schema):
    id: int
    date: datetime.date
    duration_hours: decimal.Decimal
    description: str
    billable: bool
    ownership_type: str
    client_name: str | None
    project_name: str | None
    user_name: str | None
