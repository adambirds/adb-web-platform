"""REST API views for passkey authentication security logs."""

import logging
from typing import Any

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router, Schema

from authentication.ninja.schemas import ProblemDetail
from authentication.passkeys.models import PasskeyAuthenticationLog

logger = logging.getLogger(__name__)

security_logs_router = Router(tags=["security-logs"])


class SecurityLogResponse(Schema):
    """Response schema for a single security log entry."""

    id: str
    user_email: str | None
    email: str | None
    event_type: str
    passkey_name: str | None
    ip_address: str | None
    user_agent: str
    error_message: str | None
    created_at: str


class SecurityLogsListResponse(Schema):
    """Response schema for paginated security logs."""

    items: list[SecurityLogResponse]
    pagination: dict[str, Any]


class SecurityLogsFilters(Schema):
    """Query parameters for filtering security logs."""

    page: int = 1
    page_size: int = 20
    event_type: str | None = None
    email: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    sort_by: str = "-created_at"


@security_logs_router.get(
    "",
    response={200: SecurityLogsListResponse, 403: ProblemDetail, 500: ProblemDetail},
)
def get_security_logs(
    request: HttpRequest, filters: Query[SecurityLogsFilters]
) -> tuple[int, dict[str, Any]]:
    """
    Get paginated list of passkey authentication security logs.

    Requires staff permissions.

    200: Success
    403: Forbidden (not staff)
    500: Server error
    """
    try:
        # Check staff permission
        if not request.user.is_authenticated:
            return 403, {
                "message": "Authentication required",
                "success": False,
                "code": "unauthenticated",
            }

        if not (request.user.is_staff or request.user.is_superuser):
            return 403, {
                "message": "You do not have permission to access this resource.",
                "success": False,
                "code": "forbidden",
            }

        # Build queryset
        queryset = PasskeyAuthenticationLog.objects.select_related("user", "passkey").all()

        # Apply filters
        if filters.event_type:
            queryset = queryset.filter(event_type=filters.event_type)

        if filters.email:
            queryset = queryset.filter(
                Q(email__icontains=filters.email) | Q(user__email__icontains=filters.email)
            )

        if filters.date_from:
            queryset = queryset.filter(created_at__gte=filters.date_from)

        if filters.date_to:
            queryset = queryset.filter(created_at__lte=filters.date_to)

        # Apply sorting
        sort_field = filters.sort_by
        if sort_field.lstrip("-") in [
            "created_at",
            "event_type",
            "email",
            "ip_address",
        ]:
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by("-created_at")

        # Count total
        total_count = queryset.count()

        # Apply pagination
        page = max(1, filters.page)
        page_size = min(100, max(1, filters.page_size))  # Cap at 100
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        logs = queryset[start_index:end_index]

        # Build response items
        items = []
        for log in logs:
            user_email = log.user.email if log.user else None
            passkey_name = log.passkey.name if log.passkey else None

            items.append(
                SecurityLogResponse(
                    id=str(log.id),
                    user_email=user_email,
                    email=log.email,
                    event_type=log.event_type,
                    passkey_name=passkey_name,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    error_message=log.error_message,
                    created_at=log.created_at.isoformat(),
                )
            )

        # Build pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1

        pagination = {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next_page": has_next,
            "has_previous_page": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
        }

        return 200, {
            "items": items,
            "pagination": pagination,
        }

    except Exception as e:
        logger.exception("Error fetching security logs: %s", str(e))
        return 500, {
            "message": "An error has occurred.",
            "success": False,
            "code": "server_error",
        }
