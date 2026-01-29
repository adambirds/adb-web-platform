import logging
from typing import Union

import graphene
import stripe
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.utils import timezone
from graphql import GraphQLError

from apps.payments.models import Customer
from authentication.tasks import send_verification_email
from authentication.types import UserType

logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")


class AdminLoginMutation(graphene.Mutation):
    user = graphene.Field(UserType)
    status = graphene.String()
    message = graphene.String()
    success = graphene.Boolean()
    requires_2fa = graphene.Boolean()
    challenge_token = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info: graphene.ResolveInfo, email: str, password: str) -> "AdminLoginMutation":
        from authentication.twofactor.utils import create_2fa_challenge, is_2fa_enabled

        User = get_user_model()

        # First, check if the user exists and if they are superuser or staff before authentication
        try:
            user_object = User.objects.get(email=email)
            if not (user_object.is_superuser or user_object.is_staff):
                return AdminLoginMutation(
                    user=None,
                    status="error",
                    message="You do not have permission to access this resource.",
                    success=False,
                    requires_2fa=False,
                    challenge_token=None,
                )
        except User.DoesNotExist:
            return AdminLoginMutation(
                user=None,
                status="error",
                message="The username and password entered are incorrect.",
                success=False,
                requires_2fa=False,
                challenge_token=None,
            )

        # Now we proceed with authentication (only for superuser/staff)
        user = authenticate(info.context, username=email, password=password)
        if user is not None:
            # Check if 2FA is enabled
            if is_2fa_enabled(user):
                # Create a 2FA challenge instead of logging in
                token = create_2fa_challenge(user, info.context)
                return AdminLoginMutation(
                    user=None,
                    status="2fa_required",
                    message="Two-factor authentication is required",
                    success=True,
                    requires_2fa=True,
                    challenge_token=token,
                )

            login(info.context, user)
            get_token(info.context)  # Ensure CSRF token is available for subsequent requests
            return AdminLoginMutation(
                user=user,
                status="success",
                success=True,
                requires_2fa=False,
                challenge_token=None,
            )
        else:
            return AdminLoginMutation(
                user=None,
                status="error",
                message="The username and password entered are incorrect.",
                success=False,
                requires_2fa=False,
                challenge_token=None,
            )


class LogoutUser(graphene.Mutation):
    status = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info: graphene.ResolveInfo) -> "LogoutUser":
        request = info.context
        if request.user.is_authenticated:
            logout(request)
            return LogoutUser(status="success", success=True)
        else:
            return LogoutUser(status="error", success=False)


class UpdateUser(graphene.Mutation):
    """
    This mutation is used to update user details such as first name, last name, email, etc, but not password.
    If email is updated, the user is required to verify the new email.
    Stripe customer details will be updated if first name, last name, or email is changed.
    """

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    status = graphene.String()
    message = graphene.String()

    class Arguments:
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        email = graphene.String(required=False)

    def mutate(self, info: graphene.ResolveInfo, **kwargs: str) -> "UpdateUser":
        request = info.context
        if request.user.is_authenticated:
            user = request.user
            updated_fields = {}

            # Check for updates in first_name, last_name, or email
            if (
                "first_name" in kwargs
                and kwargs["first_name"]
                and kwargs["first_name"] != user.first_name
            ):
                user.first_name = kwargs["first_name"]
                updated_fields["first_name"] = kwargs["first_name"]

            if (
                "last_name" in kwargs
                and kwargs["last_name"]
                and kwargs["last_name"] != user.last_name
            ):
                user.last_name = kwargs["last_name"]
                updated_fields["last_name"] = kwargs["last_name"]

            if "email" in kwargs and kwargs["email"] and kwargs["email"] != user.email:
                user.email = kwargs["email"]
                user.email_verified = False  # Reset email verification status
                user.verification_token = user.generate_verification_token()  # Generate new token
                user.last_verification_email_sent = timezone.now()
                send_verification_email.delay(user.email, user.first_name, user.verification_token)
                updated_fields["email"] = kwargs["email"]

            user.save()

            # Update the Stripe customer if relevant fields have changed
            if any(field in updated_fields for field in ["first_name", "last_name", "email"]):
                customer = Customer.objects.get(user=user)
                stripe.Customer.modify(
                    customer.stripe_customer_id,
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}",
                )

            return UpdateUser(
                user=user,
                success=True,
                status="success",
                message="User details updated successfully",
            )
        else:
            return UpdateUser(
                user=None, success=False, status="error", message="User not authenticated"
            )


class ResetUserPassword(graphene.Mutation):
    """
    This mutation is used to reset user password.
    """

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    def mutate(
        self, info: graphene.ResolveInfo, old_password: str, new_password: str
    ) -> Union["ResetUserPassword", GraphQLError]:
        request = info.context
        if request.user.is_authenticated:
            user = request.user
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return ResetUserPassword(
                    user=user, success=True, message="Password reset successfully"
                )
            else:
                return GraphQLError("Old password is incorrect")
        else:
            return GraphQLError("User not authenticated")


class Mutation(graphene.ObjectType):
    # Admin authentication still uses GraphQL (via auth service now)
    admin_login_user = AdminLoginMutation.Field()
    logout_user = LogoutUser.Field()

    # User management
    update_user = UpdateUser.Field()
    reset_user_password = ResetUserPassword.Field()
