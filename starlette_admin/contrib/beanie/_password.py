# https://github.com/pydantic/pydantic/issues/2125

import binascii
import hashlib
import os
import secrets


def generate_password() -> str:
    """Generate random password."""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    salt = b"__hash__" + hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode("ascii")


def is_hash(pw: str) -> bool:
    return pw.startswith("__hash__") and len(pw) == 200


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    salt = stored_password[:72]
    stored_password = stored_password[72:]
    pwdhash = hashlib.pbkdf2_hmac(
        "sha512", provided_password.encode("utf-8"), salt.encode("ascii"), 100000
    )
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password


class Password(str):
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            type="string", format="password", examples="x?1_P-1M.4!eM", writeOnly=True
        )

    @classmethod
    def validate(cls, v) -> str:
        if is_hash(v):
            return v
        return hash_password(v)
