import graphene
from graphene_django import DjangoObjectType

from authentication.models import User


class UserType(DjangoObjectType):
    ebay_account = graphene.Field("apps.ebay.types.EbayAccountType")

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email_verified",
            "email",
            "is_active",
            "ebay_account",
            "is_superuser",
            "is_staff",
            "date_joined",
        ]

    name = graphene.String()

    def resolve_name(self, info: graphene.ResolveInfo) -> str:
        return f"{self.first_name} {self.last_name}"


class EmailVerifiedType(graphene.ObjectType):
    email_verified = graphene.Boolean()
    message = graphene.String()
    status = graphene.String()
