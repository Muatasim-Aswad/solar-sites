import json
import sqlite3
import subprocess
from pathlib import Path

import httpx
import pytest
from conftest import ORIGIN, PASSWORD, SITE, create_site, register
from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from test_auth import assert_error

from solar_sites.config import Settings
from solar_sites.main import create_app
from solar_sites.modules.auth.models import Session, User
from solar_sites.modules.auth.routes import COOKIE_NAME
from solar_sites.modules.sites.models import Site
from solar_sites.openapi import export_schema


async def test_persistence_and_idempotent_startup(
    client: httpx.AsyncClient, app: FastAPI, settings: Settings
) -> None:
    csrf = await register(client)
    site_id = await create_site(client)
    token = client.cookies[COOKIE_NAME]
    second = create_app(settings)
    async with second.router.lifespan_context(second):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(second), base_url=ORIGIN
        ) as restored:
            restored.cookies.set(COOKIE_NAME, token)
            assert (await restored.get("/api/me")).json() == {
                "email": "advisor@example.com",
                "csrfToken": csrf,
            }
            assert (await restored.get(f"/api/sites/{site_id}")).json()["clientName"] == SITE[
                "clientName"
            ]
        async with second.state.database.sessions() as db:
            assert await db.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
            assert await db.scalar(text("PRAGMA foreign_keys")) == 1
            assert await db.scalar(text("PRAGMA journal_mode")) == "wal"
            rows = (
                await db.execute(
                    text(
                        "SELECT name, strict FROM pragma_table_list "
                        "WHERE name IN ('users','sites','sessions')"
                    )
                )
            ).all()
            assert len(rows) == 3 and all(strict == 1 for _, strict in rows)


async def test_sqlite_rejects_invalid_site_and_cascades(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    await register(client)
    site_id = await create_site(client)
    async with app.state.database.sessions() as db:
        site = (await db.scalars(select(Site))).one()
        owner = site.user_id
        for column, value in [
            ("peak_kwp", 0),
            ("latitude", 91),
            ("longitude", -181),
            ("client_name", " "),
            ("roof_area_m2", -1),
        ]:
            with pytest.raises(IntegrityError):
                await db.execute(
                    text(f"UPDATE sites SET {column} = :value WHERE id = :id"),
                    {"value": value, "id": site_id},
                )
                await db.commit()
            await db.rollback()
        with pytest.raises(IntegrityError):
            await db.execute(
                text("UPDATE sites SET user_id='missing' WHERE id=:id"), {"id": site_id}
            )
            await db.commit()
        await db.rollback()
        await db.execute(delete(User).where(User.id == owner))
        await db.commit()
        assert list(await db.scalars(select(Site))) == []
        assert list(await db.scalars(select(Session))) == []


async def test_database_rejects_invalid_session_and_duplicate_email(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    await register(client)
    async with app.state.database.sessions() as db:
        owner = (await db.scalars(select(User.id))).one()
        with pytest.raises(IntegrityError):
            db.add(
                Session(
                    session_token_hash=b"short",
                    user_id=owner,
                    csrf_token="csrf",
                    created_at=1,
                    expires_at=2,
                )
            )
            await db.commit()
        await db.rollback()
        with pytest.raises(IntegrityError):
            db.add(User(id="another", email="ADVISOR@example.com", password_hash="hash"))
            await db.commit()
        await db.rollback()


async def test_runtime_shutdown_closes_shared_resources(settings: Settings) -> None:
    app = create_app(settings)
    assert not settings.database_path.exists()
    async with app.router.lifespan_context(app):
        client = app.state.solar.client.client
        passwords = app.state.passwords
        assert not client.is_closed
    assert client.is_closed
    with pytest.raises(RuntimeError, match="shutdown"):
        await passwords.hash(password="unused")
    sqlite3.connect(settings.database_path).close()


async def test_shared_routers_use_each_applications_resources(
    client: httpx.AsyncClient, settings: Settings
) -> None:
    second_settings = settings.model_copy(
        update={
            "database_path": settings.database_path.with_name("second.sqlite3"),
            "allowed_origins": ["https://testserver"],
            "cookie_secure": True,
            "session_age_seconds": 60,
        }
    )
    second = create_app(second_settings)
    async with second.router.lifespan_context(second):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=second),
            base_url="https://testserver",
            headers={"Origin": "https://testserver"},
        ) as other_client:
            credentials = {"email": "advisor@example.com", "password": PASSWORD}
            first_response = await client.post("/api/register", json=credentials)
            second_response = await other_client.post("/api/register", json=credentials)
            assert first_response.status_code == second_response.status_code == 201
            first_cookie = first_response.headers["set-cookie"]
            second_cookie = second_response.headers["set-cookie"]
            assert "Max-Age=28800" in first_cookie and "Secure" not in first_cookie
            assert "Max-Age=60" in second_cookie and "Secure" in second_cookie

            client.headers["X-CSRF-Token"] = first_response.json()["csrfToken"]
            site_id = await create_site(client)
            assert (await client.get(f"/api/sites/{site_id}")).status_code == 200
            assert (await other_client.get("/api/sites")).json() == []
            assert (await other_client.get(f"/api/sites/{site_id}")).status_code == 404


async def test_runtime_uses_environment_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    database = tmp_path / "configured-data" / "database.sqlite3"
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<h1>Configured frontend</h1>")
    monkeypatch.setenv("DATABASE_PATH", str(database))
    monkeypatch.setenv("FRONTEND_PATH", str(frontend))
    monkeypatch.setenv("ALLOWED_HOSTS", '["env.example"]')
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://env.example"]')
    app = create_app()
    async with app.router.lifespan_context(app):
        assert database.is_file()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="http://env.example",
            headers={"Origin": "http://env.example"},
        ) as client:
            response = await client.get("/")
            assert response.status_code == 200
            assert response.text == "<h1>Configured frontend</h1>"
            assert (
                await client.post(
                    "/api/register", json={"email": "advisor@example.com", "password": PASSWORD}
                )
            ).status_code == 201


def test_openapi_export_is_deterministic_and_has_no_startup_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "should-not-exist" / "database.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(target))
    schema = export_schema()
    assert schema == export_schema()
    assert not target.parent.exists()
    data = json.loads(schema)
    paths = data["paths"]
    assert {
        "/api/register",
        "/api/login",
        "/api/logout",
        "/api/me",
        "/api/sites",
        "/api/sites/{id}",
        "/api/sites/{id}/production",
        "/api/sites/{id}/battery",
    } <= set(paths)
    assert set(data["components"]["schemas"]["SiteInput"]["properties"]) == set(SITE) | {
        "roofAreaM2"
    }
    params = paths["/api/sites/{id}/battery"]["get"]["parameters"]
    assert {param["name"] for param in params} >= {"id", "capacityKwh", "annualUseKwh"}
    output = tmp_path / "openapi.json"
    subprocess.run(["solar-sites-openapi", "--output", str(output)], check=True)
    assert output.read_text() == schema
    assert not target.parent.exists()


@pytest.mark.parametrize(
    "host", ["evil.example", "testserver.evil", "evil@testserver", "testserver/evil"]
)
async def test_host_guard(client: httpx.AsyncClient, host: str) -> None:
    assert_error(await client.get("/api/me", headers={"Host": host}), 400, "HOST_FORBIDDEN")


async def test_body_limit_including_streamed_input(client: httpx.AsyncClient) -> None:
    async def chunks():
        for _ in range(20):
            yield b"x" * 1024

    response = await client.post(
        "/api/register", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert_error(response, 413, "REQUEST_TOO_LARGE")


async def test_json_required_and_malformed_body(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/register", content="email=a&password=b", headers={"Content-Type": "text/plain"}
    )
    assert_error(response, 415, "UNSUPPORTED_MEDIA_TYPE")
    response = await client.post(
        "/api/register", content="{", headers={"Content-Type": "application/json"}
    )
    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert error["issues"]
    assert "input" not in str(error["issues"])


async def test_unknown_routes_methods_and_unexpected_errors(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    assert_error(await client.get("/api/missing"), 404, "NOT_FOUND")
    response = await client.patch("/api/me", json={})
    assert_error(response, 405, "METHOD_NOT_ALLOWED")
    assert "GET" in response.headers["allow"]

    @app.get("/api/failure")
    async def fail() -> None:
        raise RuntimeError("private-data-must-not-leak")

    response = await client.get("/api/failure")
    assert_error(response, 500, "INTERNAL_ERROR")
    assert "private-data" not in response.text


async def test_api_only_health_and_docs(client: httpx.AsyncClient) -> None:
    assert (await client.get("/healthz")).json() == {"status": "ok"}
    assert (await client.get("/readyz")).json() == {"status": "ready"}
    assert (await client.get("/docs")).status_code == 200
    assert (await client.get("/openapi.json")).status_code == 200


async def test_readiness_fails_and_recovers_without_affecting_liveness(
    client: httpx.AsyncClient, app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable_database() -> None:
        raise OSError("private database details")

    with monkeypatch.context() as patch:
        patch.setattr(app.state.database, "ping", unavailable_database)
        response = await client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "HTTP_ERROR"
        assert "private" not in response.text
        assert (await client.get("/healthz")).status_code == 200

    assert (await client.get("/readyz")).status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {"email": "invalid", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "x" * 129},
        {"email": "a@example.com", "password": 123456789012},
    ],
)
async def test_credentials_validation(client: httpx.AsyncClient, body: dict) -> None:
    response = await client.post("/api/register", json=body)
    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert error["issues"]
    assert "input" not in error


@pytest.mark.parametrize(
    "kwargs",
    [
        {"allowed_origins": []},
        {"allowed_origins": ["*"]},
        {"allowed_origins": ["http://localhost/path"]},
        {"allowed_hosts": ["*"]},
        {"session_age_seconds": 0},
        {"pvgis_loss": float("nan")},
        {"pvgis_year": 0},
        {"pvgis_concurrency": 0},
        {"pvgis_angle": 91},
    ],
)
def test_invalid_configuration(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


@pytest.mark.parametrize(
    ("path", "headers", "expected_status"),
    [
        ("/healthz", {}, 200),
        ("/api/me", {}, 401),
        ("/api/missing", {}, 404),
        ("/api/me", {"Host": "forbidden.example"}, 400),
    ],
)
async def test_request_completion_logs(
    client: httpx.AsyncClient,
    caplog: pytest.LogCaptureFixture,
    path: str,
    headers: dict[str, str],
    expected_status: int,
) -> None:
    response = await client.get(path, headers=headers)
    completions = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "solar_sites.http"
        and json.loads(record.message)["event"] == "request_completed"
    ]
    assert len(completions) == 1
    completion = completions[0]
    assert completion["request_id"] == response.headers["X-Request-ID"]
    assert completion["method"] == "GET"
    assert completion["path"] == path
    assert completion["status"] == response.status_code == expected_status
    assert completion["duration_ms"] >= 0


async def test_unexpected_error_traceback_and_request_id(
    client: httpx.AsyncClient, app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    @app.get("/api/logged-failure")
    async def fail() -> None:
        raise RuntimeError("server-only diagnostic")

    response = await client.get("/api/logged-failure?private-query=hidden")
    assert_error(response, 500, "INTERNAL_ERROR")
    exceptions = [record for record in caplog.records if record.exc_info]
    assert len(exceptions) == 1
    record = exceptions[0]
    assert json.loads(record.message)["request_id"] == response.headers["X-Request-ID"]
    assert record.exc_info[0] is RuntimeError
    assert "Traceback" in caplog.text
    assert "server-only diagnostic" in caplog.text
    assert "server-only diagnostic" not in response.text
    assert "private-query" not in caplog.text
    completion = json.loads(caplog.records[-1].message)
    assert completion["status"] == 500
