from starlette_admin.cookies import SignedCookie


def test_signed_cookie_non_timed_init():
    cookie = SignedCookie("secret", "salt")
    assert cookie._signer is not None


def test_signed_cookie_non_timed_loads():
    cookie = SignedCookie("secret", "salt")
    value = cookie.dumps("test-value")
    assert cookie.loads(value) == "test-value"


def test_signed_cookie_bad_signature_returns_none():
    cookie = SignedCookie("secret", "salt")
    assert cookie.loads("invalid-tampered-value") is None
