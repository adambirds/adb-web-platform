# Auth Service Frontend

This is the centralized authentication service frontend. It provides a single authentication endpoint for all applications.

## Features

- **Passkey-first authentication**: Login with discoverable credentials (no email required)
- **Password authentication**: Traditional email/password login as fallback
- **Two-factor authentication**: TOTP-based 2FA with recovery codes
- **Session management**: Secure session cookies
- **Security settings**: Passkey and 2FA management

## Architecture

This service implements a **redirect-based authentication flow**:

1. User visits app (localhost:3000)
2. If not authenticated, redirect to auth service (localhost:5175/login?next=...)
3. User authenticates with passkey or password
4. On success, redirect back to the `next` URL
5. Session cookie is set

## Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm run dev

# Build for production
pnpm run build
```

## API Endpoints

All endpoints are at `/api/v1/auth-service/`:

### Authentication

- `POST /login` - Login with email/password
- `POST /logout` - Logout
- `GET /me` - Get current user
- `POST /register` - Register new account
- `POST /verify-email` - Verify email with token

### Password Management

- `POST /change-password` - Change password (authenticated)
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password with token

### 2FA

- `GET /2fa/status` - Get 2FA status
- `POST /2fa/setup` - Begin 2FA setup
- `POST /2fa/confirm` - Confirm 2FA setup
- `POST /2fa/disable` - Disable 2FA
- `POST /2fa/verify` - Verify 2FA code during login
- `POST /2fa/recovery-codes` - Regenerate recovery codes

### Passkeys (WebAuthn)

- `POST /webauthn/discover-auth` - Begin discoverable credential auth
- `POST /webauthn/complete-discover-auth` - Complete discoverable auth
- `POST /webauthn/begin-register` - Begin passkey registration
- `POST /webauthn/complete-register` - Complete passkey registration
- `GET /webauthn/passkeys` - List passkeys
- `POST /webauthn/delete` - Delete passkey
- `POST /webauthn/rename` - Rename passkey

## Environment Variables

| Variable         | Description     | Default                                     |
| ---------------- | --------------- | ------------------------------------------- |
| `VITE_API_URL`   | Backend API URL | `http://localhost:8000/api/v1/auth-service` |
| `VITE_APP_URL`   | Main app URL    | `http://localhost:5173`                     |
| `VITE_ADMIN_URL` | Admin app URL   | `http://localhost:5174`                     |
| `VITE_DOCS_URL`  | Docs site URL   | `http://localhost:3001`                     |
