import logging
from typing import Any

import graphene

from authentication.types import EmailVerifiedType, UserType

logger = logging.getLogger(__name__)

__all__ = [
    "CheckEmailVerifiedQuery",
    "UserAuthenticatedQuery",
    "UserQuery",
]


class UserAuthenticatedQuery(graphene.ObjectType):
    is_authenticated = graphene.Boolean()

    def resolve_is_authenticated(self, info: graphene.ResolveInfo, **kwargs: Any) -> bool:
        request = info.context
        is_auth = request.user.is_authenticated
        logger.info(
            "[resolve_is_authenticated] is_authenticated: %s, session_key: %s",
            is_auth,
            request.session.session_key if hasattr(request, "session") else "no-session",
        )
        return is_auth


class UserQuery(graphene.ObjectType):
    user = graphene.Field(UserType)

    def resolve_user(self, info: graphene.ResolveInfo, **kwargs: Any) -> UserType | None:
        request = info.context
        logger.info(
            "[resolve_user] Checking authentication, is_authenticated: %s, session_key: %s",
            request.user.is_authenticated,
            request.session.session_key if hasattr(request, "session") else "no-session",
        )
        if request.user.is_authenticated:
            logger.info("[resolve_user] Returning user: %s", request.user.email)
            return request.user
        # Return None instead of raising an error to allow checking isAuthenticated first
        logger.info("[resolve_user] User not authenticated, returning None")
        return None


class CheckEmailVerifiedQuery(graphene.ObjectType):
    email_verified = graphene.Field(EmailVerifiedType)

    def resolve_email_verified(self, info: graphene.ResolveInfo, **kwargs: Any) -> dict[str, Any]:
        request = info.context
        if request.user.is_authenticated:
            user = request.user
            return {
                "email_verified": user.email_verified,
                "message": "Email is verified",
                "status": "success",
            }
        else:
            return {
                "email_verified": False,
                "message": "You must be logged in to access this data.",
                "status": "error",
            }
