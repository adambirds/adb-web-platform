"""Authentication schemas for Django Ninja API."""

from ninja import Schema
from pydantic import EmailStr, Field


class LoginRequest(Schema):
    """Login request schema."""

    email: EmailStr
    password: str


class ObjectScopeResponse(Schema):
    """Effective object scope for one restricted resource family."""

    all: bool = False
    ids: list[int] = Field(default_factory=list)


class AccessScopeResponse(Schema):
    """Effective object scopes used by the internal admin frontend."""

    clients: ObjectScopeResponse = Field(default_factory=ObjectScopeResponse)
    ticket_queues: ObjectScopeResponse = Field(default_factory=ObjectScopeResponse)


class UserResponse(Schema):
    """Authenticated staff user and effective access data."""

    id: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_superuser: bool
    permissions: list[str] = Field(default_factory=list)
    scope: AccessScopeResponse = Field(default_factory=AccessScopeResponse)


class AuthResponse(Schema):
    """Authentication success response."""

    user: UserResponse
    message: str = "Login successful"
    success: bool = True


class StatusResponse(Schema):
    """Generic status response schema."""

    message: str
    success: bool = True


class ProblemDetail(Schema):
    """Minimal API error response."""

    message: str
    success: bool = False
    code: str | None = None
