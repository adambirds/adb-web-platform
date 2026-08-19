import datetime
import decimal
import typing

from ninja import Schema

ClientStatus = typing.Literal["active", "inactive", "archived"]
ProjectOwnershipType = typing.Literal["client", "internal"]
ProjectStatus = typing.Literal["planning", "active", "paused", "completed", "archived"]


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


class ProjectIn(Schema):
    name: str
    description: str = ""
    status: ProjectStatus = "active"
    ownership_type: ProjectOwnershipType = "client"
    client_id: int | None = None
    start_date: datetime.date
    end_date: datetime.date | None = None
    budget: decimal.Decimal | None = None
    hourly_rate: decimal.Decimal | None = None


class ProjectDetailOut(Schema):
    id: int
    name: str
    description: str
    status: str
    ownership_type: str
    client_id: int | None
    client_name: str | None
    start_date: datetime.date
    end_date: datetime.date | None
    budget: decimal.Decimal | None
    hourly_rate: decimal.Decimal | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    task_count: int
    open_task_count: int
    time_entry_count: int
    tracked_hours: decimal.Decimal
    billable_hours: decimal.Decimal
    can_change: bool


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
