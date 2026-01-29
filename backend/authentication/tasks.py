import logging
import traceback
from email.utils import formataddr
from uuid import UUID

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from apps.ebay.clients.discord import DiscordEmbed, DiscordWebhook

logger = logging.getLogger(__name__)


def send_email_with_sendgrid(
    to_email: str, subject: str, text_template: str, html_template: str, context: dict[str, str]
) -> None:
    try:
        text_message = render_to_string(text_template, context)
        html_message = render_to_string(html_template, context)
        from_email = formataddr(
            (getattr(settings, "DEFAULT_FROM_EMAIL_NAME", ""), settings.DEFAULT_FROM_EMAIL)
        )

        email_message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=text_message,
            html_content=html_message,
        )

        sg = SendGridAPIClient(getattr(settings, "SENDGRID_API_KEY", ""))
        sg.send(email_message)

    except Exception as e:
        webhook_url = getattr(settings, "DISCORD_WEBHOOK_ERROR_LOGGING_URL", "")
        webhook = DiscordWebhook(webhook_url)

        embed = DiscordEmbed(
            title=f"{getattr(settings, 'SITE_NAME', 'App')} Email Error",
            color=0xE74C3C,
        )
        embed.set_timestamp()
        embed.set_footer(text=f"{getattr(settings, 'SITE_NAME', 'App')} Email Service")
        embed.add_embed_field(name="Context", value=f"Error sending email: {subject}")
        embed.add_embed_field(name="Email", value=to_email)
        embed.add_embed_field(name="Error Type", value=type(e).__name__, inline=True)
        embed.add_embed_field(name="Error Message", value=str(e), inline=False)

        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        tb_str = "".join(tb_lines).strip()
        embed.add_embed_field(name="Traceback", value=f"```{tb_str}```", inline=False)

        webhook.add_embed(embed)
        webhook.execute()
        logger.error("Failed to send email: %s", e)


@shared_task(queue="email")
def send_verification_email(email: str, first_name: str, verification_token: UUID) -> None:
    logger.info("Sending verification email to %s", email)
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
    subject = f"Verify your email address for {getattr(settings, 'SITE_NAME', 'App')}"
    context = {"verification_link": verification_link, "first_name": first_name}
    send_email_with_sendgrid(
        email,
        subject,
        "email/text/email_verification.txt",
        "email/html/email_verification.html",
        context,
    )


@shared_task(queue="email")
def send_missing_initial_verification_email(
    email: str, first_name: str, verification_token: UUID
) -> None:
    logger.info("Sending initial verification email to %s", email)
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
    subject = f"Please verify your {getattr(settings, 'SITE_NAME', 'App')} account"
    context = {
        "verification_link": verification_link,
        "first_name": first_name,
    }

    send_email_with_sendgrid(
        to_email=email,
        subject=subject,
        text_template="email/text/missing_initial_verification.txt",
        html_template="email/html/missing_initial_verification.html",
        context=context,
    )


@shared_task(queue="email")
def send_reset_password_email(email: str, first_name: str, reset_password_link: str) -> None:
    logger.info("Sending reset password email to %s", email)
    subject = f"Reset your password for {getattr(settings, 'SITE_NAME', 'App')}"
    context = {"reset_link": reset_password_link, "first_name": first_name}
    send_email_with_sendgrid(
        email, subject, "email/text/reset_password.txt", "email/html/reset_password.html", context
    )


@shared_task(queue="email")
def send_email_verification_successful_email(email: str, first_name: str) -> None:
    logger.info("Sending email verification successful email to %s", email)
    subject = "Email verification successful"
    context = {"first_name": first_name}
    send_email_with_sendgrid(
        email,
        subject,
        "email/text/email_verification_successful.txt",
        "email/html/email_verification_successful.html",
        context,
    )


@shared_task(queue="email")
def send_password_reset_successful_email(email: str, first_name: str) -> None:
    logger.info("Sending password reset successful email to %s", email)
    subject = "Password reset successful"
    context = {"first_name": first_name}
    send_email_with_sendgrid(
        email,
        subject,
        "email/text/reset_password_successful.txt",
        "email/html/reset_password_successful.html",
        context,
    )


@shared_task(queue="general")
def notify_new_user_signup(user_email: str) -> None:
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_SIGNUP_URL", "")
    webhook = DiscordWebhook(webhook_url)
    webhook.set_content(f"New user signup: {user_email}")
    webhook.execute()


@shared_task(queue="general")
def notify_user_email_verified(user_email: str) -> None:
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_SIGNUP_URL", "")
    webhook = DiscordWebhook(webhook_url)
    webhook.set_content(f"User email verified: {user_email}")
    webhook.execute()
