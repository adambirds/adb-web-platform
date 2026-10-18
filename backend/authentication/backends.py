from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from authentication.models import User


class EmailBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            assert password is not None
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            else:
                return None

    def has_perm(self, user_obj: User | AnonymousUser, perm: str, obj: Any = None) -> bool:
        # Keep one identity backend: existing login/MFA flows can safely infer it.
        if obj is not None:
            from apps.analytics.access import business_has_perm
            from apps.analytics.models import Business

            if isinstance(obj, Business):
                return business_has_perm(user_obj, perm, obj)
        return super().has_perm(user_obj, perm, obj)
