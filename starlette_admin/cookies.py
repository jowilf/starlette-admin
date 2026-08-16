from __future__ import annotations

from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer, URLSafeTimedSerializer


class SignedCookie:
    """Signs and verifies cookie values using itsdangerous.

    Wraps `URLSafeSerializer` for untimed signatures or
    `URLSafeTimedSerializer` when `timed=True`, so callers don't need to
    pick the serializer class themselves.
    """

    def __init__(
        self,
        secret_key: str,
        salt: str,
        *,
        timed: bool = False,
        max_age: int | None = None,
    ) -> None:
        self._max_age = max_age
        if timed:
            self._signer: URLSafeSerializer | URLSafeTimedSerializer = (
                URLSafeTimedSerializer(secret_key, salt=salt)
            )
        else:
            self._signer = URLSafeSerializer(secret_key, salt=salt)

    def dumps(self, value: Any) -> str:
        """Serialize and sign *value*, returning the cookie-safe string to store."""
        return self._signer.dumps(value)

    def loads(self, value: str) -> Any:
        """Verify and deserialize a signed cookie value.

        Returns `None` if the signature is invalid, expired (when `timed=True`
        and `max_age` is set), or otherwise malformed, instead of raising.
        """
        try:
            if isinstance(self._signer, URLSafeTimedSerializer):
                return self._signer.loads(value, max_age=self._max_age)
            return self._signer.loads(value)
        except BadSignature:
            return None
