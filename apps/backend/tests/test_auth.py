import hashlib
import time

import httpx
import pytest
from conftest import PASSWORD, SITE, register
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.config import Settings
from solar_sites.main import create_app
from solar_sites.modules.auth import repository
from solar_sites.modules.auth.models import Session, User
from solar_sites.modules.auth.routes import COOKIE_NAME


def assert_error(response: httpx.Response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    body = response.json()["error"]
    assert body["status"] == status
    assert body["code"] == code
    assert body["message"]
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"
    return body


async def test_registration_login_logout(client: httpx.AsyncClient, app: FastAPI) -> None:
    csrf = await register(client, "Advisor@Example.com")
    token = client.cookies[COOKIE_NAME]
    assert token != csrf
    response = await client.get("/api/me")
    assert response.json() == {"email": "advisor@example.com", "csrfToken": csrf}
    async with app.state.database.sessions() as db:
        session = (await db.scalars(select(Session))).one()
        user = (await db.scalars(select(User))).one()
        assert session.session_token_hash == hashlib.sha256(token.encode()).digest()
        assert session.csrf_token == csrf
        assert session.expires_at - session.created_at == 8 * 3600
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash
    response = await client.post("/api/logout")
    assert response.status_code == 204 and response.content == b""
    assert "Max-Age=0" in response.headers["set-cookie"]
    client.cookies.set(COOKIE_NAME, token, domain="testserver.local", path="/")
    assert_error(await client.get("/api/me"), 401, "UNAUTHENTICATED")
    response = await client.post(
        "/api/login", json={"email": "ADVISOR@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["csrfToken"] != csrf
    assert client.cookies[COOKIE_NAME] != token


async def test_registration_rolls_back_when_session_persistence_fails(
    client: httpx.AsyncClient, app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_session = repository.add_session

    async def fail_after_session_write(db: AsyncSession, *, session: Session) -> None:
        await add_session(db, session=session)
        raise RuntimeError("Session persistence failed")

    with monkeypatch.context() as patch:
        patch.setattr(repository, "add_session", fail_after_session_write)
        response = await client.post(
            "/api/register", json={"email": "advisor@example.com", "password": PASSWORD}
        )
        assert_error(response, 500, "INTERNAL_ERROR")

    async with app.state.database.sessions() as db:
        assert await db.scalar(select(User)) is None
        assert await db.scalar(select(Session)) is None

    await register(client)


async def test_cookie_attributes(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/register", json={"email": "a@example.com", "password": PASSWORD}
    )
    cookie = response.headers["set-cookie"]
    for flag in ["HttpOnly", "SameSite=lax", "Path=/", "Max-Age=28800"]:
        assert flag in cookie
    assert "Secure" not in cookie


async def test_secure_https_cookie(settings: Settings) -> None:
    settings.allowed_origins = ["https://testserver"]
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="https://testserver",
            headers={"Origin": "https://testserver"},
        ) as client:
            response = await client.post(
                "/api/register", json={"email": "a@example.com", "password": PASSWORD}
            )
            assert response.status_code == 201
            assert "Secure" in response.headers["set-cookie"]


async def test_duplicate_email_and_wrong_credentials(client: httpx.AsyncClient) -> None:
    await register(client)
    assert_error(
        await client.post(
            "/api/register", json={"email": "ADVISOR@example.com", "password": PASSWORD}
        ),
        409,
        "EMAIL_EXISTS",
    )
    for email in ["advisor@example.com", "unknown@example.com"]:
        response = await client.post(
            "/api/login", json={"email": email, "password": "wrong password 123"}
        )
        assert_error(response, 401, "INVALID_CREDENTIALS")
        assert "password" not in str(response.json().get("details", ""))


async def test_login_rotates_and_revokes_previous_session(client: httpx.AsyncClient) -> None:
    await register(client)
    token = client.cookies[COOKIE_NAME]
    response = await client.post(
        "/api/login", json={"email": "advisor@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, token)
    assert_error(await client.get("/api/me"), 401, "UNAUTHENTICATED")


async def test_fixed_session_expiry(client: httpx.AsyncClient, app: FastAPI) -> None:
    await register(client)
    async with app.state.database.sessions() as db:
        session = (await db.scalars(select(Session))).one()
        expiry = session.expires_at
    app.state.settings.session_age_seconds = 60
    assert (await client.get("/api/me")).status_code == 200
    async with app.state.database.sessions() as db:
        session = (await db.scalars(select(Session))).one()
        assert session.expires_at == expiry
        await db.execute(
            update(Session).values(created_at=int(time.time()) - 100, expires_at=int(time.time()))
        )
        await db.commit()
    assert_error(await client.get("/api/me"), 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("token", [None, "wrong", "ü", "x" * 1000])
async def test_csrf_writes_and_logout(client: httpx.AsyncClient, token: str | None) -> None:
    await register(client)
    client.headers.pop("X-CSRF-Token")
    if token is not None:
        client.headers = httpx.Headers(
            [*client.headers.raw, (b"X-CSRF-Token", token.encode("utf-8"))]
        )
    assert_error(await client.post("/api/sites", json=SITE), 403, "CSRF_FAILED")
    assert_error(await client.post("/api/logout"), 403, "CSRF_FAILED")
    assert (await client.get("/api/me")).status_code == 200


@pytest.mark.parametrize(
    "origin", [None, "null", "http://evil.example", "http://testserver.evil", "http://testserver/"]
)
async def test_origin_required_on_register_login(
    client: httpx.AsyncClient, origin: str | None
) -> None:
    client.headers.pop("Origin")
    if origin is not None:
        client.headers["Origin"] = origin
    for route in ["/api/register", "/api/login"]:
        assert_error(
            await client.post(route, json={"email": "a@example.com", "password": PASSWORD}),
            403,
            "ORIGIN_FORBIDDEN",
        )


async def test_origin_required_on_authenticated_write(client: httpx.AsyncClient) -> None:
    await register(client)
    client.headers["Origin"] = "https://evil.example"
    assert_error(await client.post("/api/sites", json=SITE), 403, "ORIGIN_FORBIDDEN")


@pytest.mark.parametrize(
    "path",
    [
        "/api/me",
        "/api/sites",
        "/api/sites/unknown",
        "/api/sites/unknown/production",
        "/api/sites/unknown/battery?capacityKwh=1&annualUseKwh=1",
    ],
)
async def test_unauthenticated_reads(client: httpx.AsyncClient, path: str) -> None:
    assert_error(await client.get(path), 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("token", ["invalid", "x" * 200, ""])
async def test_invalid_cookie(client: httpx.AsyncClient, token: str) -> None:
    client.cookies.set(COOKIE_NAME, token)
    assert_error(await client.get("/api/me"), 401, "UNAUTHENTICATED")


async def test_no_password_or_token_in_database_file(
    client: httpx.AsyncClient, settings: Settings
) -> None:
    await register(client)
    raw = b"".join(p.read_bytes() for p in settings.database_path.parent.glob("database.sqlite3*"))
    assert PASSWORD.encode() not in raw
    assert client.cookies[COOKIE_NAME].encode() not in raw


@pytest.mark.parametrize("email", ["advisor@example.com", "missing@example.com"])
async def test_database_connections_released_before_password_verification(
    client: httpx.AsyncClient, app: FastAPI, monkeypatch: pytest.MonkeyPatch, email: str
) -> None:
    await register(client)
    passwords = app.state.passwords
    original_verify = passwords.verify
    verified = False

    async def verify(*, password: str, hashed: str) -> bool:
        nonlocal verified
        assert app.state.database.engine.pool.checkedout() == 0
        verified = True
        return await original_verify(password=password, hashed=hashed)

    monkeypatch.setattr(passwords, "verify", verify)
    response = await client.post("/api/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == (200 if email == "advisor@example.com" else 401)
    assert verified
