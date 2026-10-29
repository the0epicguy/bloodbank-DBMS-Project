"""
Tests for password hashing, JWT tokens and role checks (Person 4).
No database needed.

Run:  cd backend && python -m pytest tests/test_auth.py -v
"""

import time
from types import SimpleNamespace

import jwt
import pytest

from app.core.config import settings
from app.core.errors import Forbidden, Unauthorized
from app.core.security import (
    create_access_token, decode_token, hash_password, require_roles, verify_password,
)


class TestPasswords:
    def test_hash_is_not_plaintext_and_verifies(self):
        h = hash_password("secret123")
        assert h != "secret123"
        assert verify_password("secret123", h)

    def test_wrong_password_rejected(self):
        assert not verify_password("nope", hash_password("secret123"))

    def test_same_password_gives_different_hashes(self):
        assert hash_password("abc12345") != hash_password("abc12345")  # random salt

    def test_garbage_hash_does_not_crash(self):
        assert not verify_password("x", "not-a-bcrypt-hash")


class TestTokens:
    def test_roundtrip(self):
        payload = decode_token(create_access_token(7, "ADMIN"))
        assert payload["sub"] == "7"
        assert payload["role"] == "ADMIN"

    def test_expired_token_rejected(self):
        token = create_access_token(1, "ADMIN", expires_minutes=-1)
        with pytest.raises(Unauthorized):
            decode_token(token)

    def test_tampered_token_rejected(self):
        token = create_access_token(1, "DONOR")
        with pytest.raises(Unauthorized):
            decode_token(token[:-3] + "abc")

    def test_token_signed_with_other_secret_rejected(self):
        forged = jwt.encode({"sub": "1", "role": "ADMIN", "exp": time.time() + 60},
                            "attacker-secret", algorithm="HS256")
        with pytest.raises(Unauthorized):
            decode_token(forged)

    def test_garbage_rejected(self):
        with pytest.raises(Unauthorized):
            decode_token("not.a.token")


class TestRoles:
    def _check(self, role, *allowed):
        checker = require_roles(*allowed)
        return checker(SimpleNamespace(role=role))

    def test_allowed_role_passes(self):
        assert self._check("ADMIN", "ADMIN", "BANK_STAFF").role == "ADMIN"

    def test_other_role_gets_403(self):
        with pytest.raises(Forbidden):
            self._check("DONOR", "ADMIN", "BANK_STAFF")
