# Advanced 02: OAuth2 / OIDC Authentication

Demonstrates how to use `OAuthProvider` to add sign-in via any OIDC-compatible provider (Auth0, Okta, Google, Keycloak, …). Authlib handles the redirect, state/PKCE, and token exchange; you only implement three methods.

## What it shows

### `OIDCAuthProvider(OAuthProvider)`

| Method | Responsibility |
|---|---|
| `get_redirect_url` | Calls `authorize_redirect`, extracts the authorization URL from the response, and returns it. The framework redirects the browser there. |
| `handle_callback` | Called when the browser returns with the auth code. Exchanges it for tokens and stores `userinfo` in the encrypted session cookie. |
| `authenticate` | Called on every request. Reads `userinfo` from the session to decide whether the request is authenticated. |
| `logout` | Clears the session cookie. |

### SessionMiddleware

Authlib stores the OAuth state nonce in the session between the initial redirect and the callback. The same session cookie carries `userinfo` after login. `SessionMiddleware` must be added **before** mounting the admin, and its `secret_key` must be kept private.

## Quick setup with Auth0

1. Create a free account at [auth0.com](https://auth0.com) and create a new **Regular Web Application**.
2. In the application settings, add `http://localhost:8000/admin/oauth/callback` to **Allowed Callback URLs**.
3. Note your **Domain**, **Client ID**, and **Client Secret**.
4. Export environment variables:

```bash
export OAUTH_CLIENT_ID="your-client-id"
export OAUTH_CLIENT_SECRET="your-client-secret"
export OAUTH_SERVER_METADATA_URL="https://your-domain.auth0.com/.well-known/openid-configuration"
export SECRET_KEY="change-me-in-production"
```

### Other providers

| Provider | `OAUTH_SERVER_METADATA_URL` |
|---|---|
| Auth0 | `https://{domain}.auth0.com/.well-known/openid-configuration` |
| Okta | `https://{domain}.okta.com/.well-known/openid-configuration` |
| Google | `https://accounts.google.com/.well-known/openid-configuration` |
| Keycloak | `https://{host}/realms/{realm}/.well-known/openid-configuration` |

## Run

```bash
cd examples/advanced/02-oauth2
uv run app.py
```

Then open <http://localhost:8000/admin/>. You will be redirected to your provider's login page and returned to the admin after a successful sign-in.

## OAuth2 flow diagram

```
Browser          starlette-admin          OIDC Provider
   │                    │                      │
   │  GET /admin/       │                      │
   │──────────────────► │                      │
   │  302 → /login      │                      │
   │◄────────────────── │                      │
   │                    │                      │
   │  GET /login        │                      │
   │──────────────────► │                      │
   │   get_redirect_url()  ─ authorize_redirect()
   │  303 → provider    │                      │
   │◄────────────────── │                      │
   │                    │                      │
   │  GET /authorize    │                      │
   │─────────────────────────────────────────► │
   │  (user logs in)                           │
   │  302 → /admin/oauth/callback?code=…       │
   │◄───────────────────────────────────────── │
   │                    │                      │
   │  GET /oauth/callback                      │
   │──────────────────► │                      │
   │                handle_callback()          │
   │                authorize_access_token() ──►
   │                    │◄── token + userinfo ─│
   │                    │  session["user"] = … │
   │  303 → /admin/     │                      │
   │◄────────────────── │                      │
   │                    │                      │
   │  GET /admin/       │                      │
   │──────────────────► │                      │
   │                authenticate()             │
   │                    │  reads session       │
   │  200 OK            │                      │
   │◄────────────────── │                      │
```
