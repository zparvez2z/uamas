from __future__ import annotations

import asyncio
from http.cookies import SimpleCookie

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app import main as app_main
from reliable_genai.security import (
    AdminLoginRequired,
    SecurityManager,
    SecuritySettings,
)


ADMIN_TOKEN = "admin-" + "a" * 40
API_TOKEN = "api-" + "b" * 40
SESSION_SECRET = "session-" + "c" * 40


def _request(
    path: str = "/",
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> Request:
    encoded_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": encoded_headers,
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 443),
        },
        receive=receive,
    )


def _session_cookie(manager: SecurityManager) -> str:
    response = Response()
    manager.issue_admin_cookie(response)
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    return cookie["uamas_admin_session"].value


def _production_settings(**overrides: str) -> SecuritySettings:
    values = {
        "UAMAS_ENV": "production",
        "UAMAS_ADMIN_TOKEN": ADMIN_TOKEN,
        "UAMAS_API_TOKEN": API_TOKEN,
        "UAMAS_SESSION_SECRET": SESSION_SECRET,
        "UAMAS_COOKIE_SECURE": "true",
        "UAMAS_ALLOWED_HOSTS": "testserver",
    }
    values.update(overrides)
    return SecuritySettings.from_env(values)


def test_development_security_is_disabled_by_default() -> None:
    settings = SecuritySettings.from_env({})

    assert settings.environment == "development"
    assert settings.auth_enabled is False
    assert settings.docs_enabled is True


def test_production_security_fails_closed_for_missing_or_weak_secrets() -> None:
    with pytest.raises(RuntimeError, match="required secrets are missing"):
        SecuritySettings.from_env(
            {
                "UAMAS_ENV": "production",
                "UAMAS_ALLOWED_HOSTS": "example.com",
            }
        )

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        _production_settings(UAMAS_API_TOKEN="short")

    with pytest.raises(RuntimeError, match="must be distinct"):
        _production_settings(UAMAS_API_TOKEN=ADMIN_TOKEN)

    with pytest.raises(RuntimeError, match="UAMAS_ALLOWED_HOSTS"):
        _production_settings(UAMAS_ALLOWED_HOSTS="")


def test_protected_routes_require_expected_credentials() -> None:
    manager = SecurityManager(_production_settings())
    with pytest.raises(AdminLoginRequired):
        manager.require_admin(_request("/dashboard"))

    with pytest.raises(HTTPException) as missing:
        manager.require_api(_request("/api/metrics"))
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as wrong:
        manager.require_api(
            _request(
                "/api/metrics",
                headers={"Authorization": "Bearer wrong"},
            )
        )
    assert wrong.value.status_code == 401

    manager.require_api(
        _request(
            "/api/metrics",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
    )
    manager.require_operator(
        _request(
            "/api/metrics",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
    )


def test_admin_login_session_and_csrf_controls() -> None:
    manager = SecurityManager(_production_settings())
    assert manager.authenticate_admin_token("wrong") is False
    assert manager.authenticate_admin_token(ADMIN_TOKEN) is True

    cookie = _session_cookie(manager)
    authenticated = _request(
        "/dashboard",
        headers={"Cookie": f"uamas_admin_session={cookie}"},
    )
    manager.require_admin(authenticated)
    csrf_token = manager.csrf_token(authenticated)
    assert csrf_token

    missing_request = _request(
        "/admin/logout",
        method="POST",
        headers={
            "Cookie": f"uamas_admin_session={cookie}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body=b"",
    )
    with pytest.raises(HTTPException) as missing:
        asyncio.run(manager.require_csrf(missing_request))
    assert missing.value.status_code == 403

    valid_body = f"csrf_token={csrf_token}".encode("ascii")
    valid_request = _request(
        "/admin/logout",
        method="POST",
        headers={
            "Cookie": f"uamas_admin_session={cookie}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(valid_body)),
        },
        body=valid_body,
    )
    asyncio.run(manager.require_csrf(valid_request))

    tampered = cookie[:-1] + ("a" if cookie[-1] != "a" else "b")
    assert manager.is_admin_session(
        _request(
            "/dashboard",
            headers={"Cookie": f"uamas_admin_session={tampered}"},
        )
    ) is False


def test_production_predict_errors_are_sanitized(monkeypatch) -> None:
    manager = SecurityManager(_production_settings())
    monkeypatch.setattr(app_main, "security", manager)

    def fail_prediction(_payload):
        raise RuntimeError("provider leaked sensitive internals")

    monkeypatch.setattr(app_main.review_graph, "predict", fail_prediction)

    request = _request("/predict", method="POST")
    request.state.request_id = "request-123"
    response = app_main.predict(
        request,
        title="test",
        description="",
    )

    assert response.status_code == 400
    body = response.body.decode("utf-8")
    assert "Request failed. Reference:" in body
    assert "provider leaked sensitive internals" not in body
    assert "request-123" in body


def test_diagnostics_do_not_expose_token_prefix(monkeypatch) -> None:
    secret = "github_pat_" + "x" * 40
    monkeypatch.setenv("GITHUB_TOKEN", secret)

    diagnostics = app_main.build_diagnostics()

    assert diagnostics["token_present"] is True
    assert "token_prefix" not in diagnostics
    assert secret not in str(diagnostics)


def test_request_body_limit_is_enforced(monkeypatch) -> None:
    settings = SecuritySettings.from_env(
        {
            "UAMAS_ENV": "development",
            "UAMAS_MAX_REQUEST_BYTES": "10",
        }
    )
    monkeypatch.setattr(app_main, "security", SecurityManager(settings))

    request = _request(
        "/admin/login",
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": "11",
        },
        body=b"x" * 11,
    )

    async def call_next(_request):
        return Response("should not execute")

    response = asyncio.run(
        app_main.apply_security_controls(request, call_next)
    )

    assert response.status_code == 413
    assert response.body == b'{"detail":"request body too large"}'
    assert response.headers["x-content-type-options"] == "nosniff"
