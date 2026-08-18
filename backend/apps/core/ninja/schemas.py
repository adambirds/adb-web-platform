from datetime import date, datetime

from ninja import Schema


class BrandOut(Schema):
    id: int
    name: str
    slug: str
    domain: str
    is_active: bool


class DashboardLeadOut(Schema):
    id: int
    name: str
    company: str
    status: str
    brand: str
    created_at: datetime


class DashboardTaskOut(Schema):
    id: int
    title: str
    status: str
    priority: int
    due_date: date | None


class DashboardActivityOut(Schema):
    id: int
    action: str
    target_label: str
    created_at: datetime


class DashboardSummaryOut(Schema):
    active_clients: int
    active_projects: int
    open_leads: int
    open_tasks: int
    overdue_tasks: int
    hours_this_week: float
    expiring_domains: int
    renewing_licences: int
    recent_leads: list[DashboardLeadOut]
    upcoming_tasks: list[DashboardTaskOut]
    recent_activity: list[DashboardActivityOut]
