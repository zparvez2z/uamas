from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import quote

from fastapi import HTTPException, Request
from starlette.responses import Response


SESSION_COOKIE_NAME = "uamas_admin_session"
MIN_SECRET_LENGTH = 32


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def _read_env(environ: Mapping[str, str], name: str, default: str = "") -> str:
    return environ.get(name, default).strip()


@dataclass(frozen=True)
class SecuritySettings:
    environment: str
    auth_enabled: bool
    admin_token: str
    api_token: str
    session_secret: str
    cookie_secure: bool
    session_ttl_seconds: int
    max_request_bytes: int
    allowed_hosts: tuple[str, ...]

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def docs_enabled(self) -> bool:
        return not self.production

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> SecuritySettings:
        values = os.environ if environ is None else environ
        environment = _read_env(values, "UAMAS_ENV", "development").lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError(f"invalid UAMAS_ENV: {environment}")

        production = environment == "production"
        auth_enabled = production or _parse_bool(
            values.get("UAMAS_AUTH_ENABLED"),
            default=False,
        )
        settings = cls(
            environment=environment,
            auth_enabled=auth_enabled,
            admin_token=_read_env(values, "UAMAS_ADMIN_TOKEN"),
            api_token=_read_env(values, "UAMAS_API_TOKEN"),
            session_secret=_read_env(values, "UAMAS_SESSION_SECRET"),
            cookie_secure=_parse_bool(
                values.get("UAMAS_COOKIE_SECURE"),
                default=production,
            ),
            session_ttl_seconds=int(
                _read_env(values, "UAMAS_SESSION_TTL_SECONDS", "28800")
            ),
            max_request_bytes=int(
                _read_env(values, "UAMAS_MAX_REQUEST_BYTES", "1000000")
            ),
            allowed_hosts=tuple(
                host.strip()
                for host in _read_env(values, "UAMAS_ALLOWED_HOSTS").split(",")
                if host.strip()
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.session_ttl_seconds <= 0:
            raise ValueError("UAMAS_SESSION_TTL_SECONDS must be positive")
        if self.max_request_bytes <= 0:
            raise ValueError("UAMAS_MAX_REQUEST_BYTES must be positive")
        if not self.auth_enabled:
            return

        required = {
            "UAMAS_ADMIN_TOKEN": self.admin_token,
            "UAMAS_API_TOKEN": self.api_token,
            "UAMAS_SESSION_SECRET": self.session_secret,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "authentication is enabled but required secrets are missing: "
                + ", ".join(missing)
            )
        weak = [name for name, value in required.items() if len(value) < MIN_SECRET_LENGTH]
        if weak:
            raise RuntimeError(
                "authentication secrets must be at least "
                f"{MIN_SECRET_LENGTH} characters: "
                + ", ".join(weak)
            )
        if len(set(required.values())) != len(required):
            raise RuntimeError("admin, API, and session secrets must be distinct")
        if self.production and not self.cookie_secure:
            raise RuntimeError("UAMAS_COOKIE_SECURE must be true in production")
        if self.production and not self.allowed_hosts:
            raise RuntimeError("UAMAS_ALLOWED_HOSTS is required in production")


class AdminLoginRequired(Exception):
    def __init__(self, next_path: str) -> None:
        self.next_path = next_path
        super().__init__(next_path)


class SecurityManager:
    def __init__(self, settings: SecuritySettings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return self.settings.auth_enabled

    def authenticate_admin_token(self, candidate: str) -> bool:
        if not self.enabled:
            return True
        return secrets.compare_digest(candidate, self.settings.admin_token)

    def require_api(self, request: Request) -> None:
        if not self.enabled:
            return
        token = self._bearer_token(request)
        if token is None or not secrets.compare_digest(token, self.settings.api_token):
            raise HTTPException(
                status_code=401,
                detail="authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def require_operator(self, request: Request) -> None:
        if not self.enabled:
            return
        if self.is_admin_session(request):
            return
        self.require_api(request)

    def require_admin(self, request: Request) -> None:
        if not self.enabled or self.is_admin_session(request):
            return
        path = request.url.path
        if request.url.query:
            path += f"?{request.url.query}"
        raise AdminLoginRequired(path)

    async def require_csrf(self, request: Request) -> None:
        if not self.enabled:
            return
        session = self._read_session(request)
        if session is None:
            raise AdminLoginRequired(request.url.path)
        form = await request.form()
        candidate = str(form.get("csrf_token", ""))
        expected = str(session.get("csrf", ""))
        if not candidate or not secrets.compare_digest(candidate, expected):
            raise HTTPException(status_code=403, detail="invalid CSRF token")

    def csrf_token(self, request: Request) -> str:
        session = self._read_session(request)
        return str(session.get("csrf", "")) if session else ""

    def issue_admin_cookie(self, response: Response) -> None:
        now = int(time.time())
        payload = {
            "exp": now + self.settings.session_ttl_seconds,
            "csrf": secrets.token_urlsafe(32),
        }
        encoded = self._encode_payload(payload)
        signature = self._sign(encoded)
        response.set_cookie(
            SESSION_COOKIE_NAME,
            f"{encoded}.{signature}",
            max_age=self.settings.session_ttl_seconds,
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite="strict",
            path="/",
        )

    def clear_admin_cookie(self, response: Response) -> None:
        response.delete_cookie(
            SESSION_COOKIE_NAME,
            path="/",
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite="strict",
        )

    def is_admin_session(self, request: Request) -> bool:
        return not self.enabled or self._read_session(request) is not None

    def login_redirect(self, next_path: str) -> str:
        safe_path = self.safe_next_path(next_path)
        return f"/admin/login?next={quote(safe_path, safe='/?=&')}"

    @staticmethod
    def safe_next_path(candidate: str | None) -> str:
        if not candidate or not candidate.startswith("/") or candidate.startswith("//"):
            return "/"
        return candidate

    def add_response_headers(self, response: Response, *, sensitive: bool) -> None:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; img-src 'self' data:; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'",
        )
        if sensitive:
            response.headers.setdefault("Cache-Control", "no-store")

    def _read_session(self, request: Request) -> dict[str, object] | None:
        if not self.enabled:
            return {"exp": int(time.time()) + 60, "csrf": ""}
        raw = request.cookies.get(SESSION_COOKIE_NAME)
        if not raw or "." not in raw:
            return None
        encoded, signature = raw.rsplit(".", 1)
        if not secrets.compare_digest(signature, self._sign(encoded)):
            return None
        try:
            payload = self._decode_payload(encoded)
            expires_at = int(payload["exp"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if expires_at <= int(time.time()):
            return None
        return payload

    def _sign(self, encoded_payload: str) -> str:
        digest = hmac.new(
            self.settings.session_secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        )
        return digest.hexdigest()

    @staticmethod
    def _encode_payload(payload: dict[str, object]) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_payload(encoded: str) -> dict[str, object]:
        padding = "=" * (-len(encoded) % 4)
        raw = base64.urlsafe_b64decode(encoded + padding)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("session payload must be an object")
        return value

    @staticmethod
    def _bearer_token(request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token:
            return None
        return token.strip()
