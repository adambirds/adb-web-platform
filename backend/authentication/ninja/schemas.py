"""Authentication schemas for Django Ninja API."""

from ninja import Schema
from pydantic import EmailStr


class LoginRequest(Schema):
    """Login request schema."""

    email: EmailStr
    password: str


class UserResponse(Schema):
    """User response schema."""

    id: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    author: dict[str, str | None] | None = None


class AuthResponse(Schema):
    """Authentication success response."""

    user: UserResponse
    message: str = "Login successful"
    success: bool = True


class StatusResponse(Schema):
    """Generic status response schema (success)."""

    message: str
    success: bool = True


class ProblemDetail(Schema):
    """
    Minimal error schema (inspired by RFC 7807, but smaller).
    Keep 'message' to match your frontend expectations.
    """

    message: str
    success: bool = False
    # Optional fields you can populate if useful:
    code: str | None = None  # e.g., "invalid_credentials", "forbidden"
