from datetime import date

from ninja import Schema


class TaskSummaryOut(Schema):
    id: int
    title: str
    status: str
    priority: int
    due_date: date | None
    ownership_type: str
    client_name: str | None
    project_name: str | None
    task_list_name: str | None
