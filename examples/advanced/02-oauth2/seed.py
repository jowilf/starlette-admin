from app import Post
from sqlalchemy.orm import Session


def seed(session: Session) -> None:
    session.add_all(
        [
            Post(
                title="Welcome to the OAuth2 example",
                body=(
                    "Sign in via your OIDC provider to manage these posts. "
                    "Your name and avatar are pulled from the token's userinfo claim."
                ),
            ),
            Post(
                title="How the flow works",
                body=(
                    "1. /login redirects you to the provider's authorization endpoint. \n"
                    "2. After you authenticate, the provider redirects back to /admin/oauth/callback. \n"
                    "3. Authlib exchanges the code for tokens; we store userinfo in an encrypted session cookie. \n"
                    "4. Every subsequent request checks the cookie, no database lookup needed.\n"
                ),
            ),
            Post(
                title="Switching providers",
                body=(
                    "Change OAUTH_SERVER_METADATA_URL to point at any OIDC-compatible provider: \n"
                    "Okta, Google, Keycloak, GitHub (via an OIDC proxy), and so on. \n"
                    "The OIDCAuthProvider code stays the same."
                ),
            ),
        ]
    )
    session.commit()
