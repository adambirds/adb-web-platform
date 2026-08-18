@auth_service_router.post("/2fa/setup", response={200: dict})
def begin_2fa_setup(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    """Begin 2FA setup - generate secret and QR code."""
    if not request.user.is_authenticated:
        return 200, {"success": False, "message": "Not authenticated"}

    try:
        import base64

        # Generate a new secret
        secret = base64.b32encode(secrets.token_bytes(20)).decode("utf-8")

        # Create or update TOTP method (unverified)
        TwoFactorMethod.objects.update_or_create(
            user=request.user,
            method_type="totp",
            defaults={
                "secret": secret,
                "is_verified": False,
                "name": "Authenticator App",
            },
        )

        # Generate otpauth URI for QR code
        issuer = getattr(settings, "SITE_NAME", "App")
        account_name = request.user.email
        qr_uri = f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}"

        return 200, {
            "success": True,