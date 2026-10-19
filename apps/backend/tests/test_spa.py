from pathlib import Path

import httpx
import pytest

from solar_sites.config import Settings
from solar_sites.main import create_app


@pytest.fixture
async def spa(tmp_path: Path):
    frontend = tmp_path / "frontend"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text('<div id="root">Application</div>')
    (frontend / "assets" / "app-123.js").write_text("console.log('application')")
    secret = tmp_path / "secret.txt"
    secret.write_text("private sentinel")
    (frontend / "assets" / "secret.txt").symlink_to(secret)
    settings = Settings(frontend_path=frontend, database_path=tmp_path / "db.sqlite3")
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://localhost:8000"
        ) as client:
            yield client


@pytest.mark.parametrize(
    "path", ["/", "/login", "/register", "/sites", "/sites/new", "/sites/123/edit", "/sites/123"]
)
async def test_known_client_routes_return_uncached_html(spa: httpx.AsyncClient, path: str) -> None:
    response = await spa.get(path)
    assert response.status_code == 200
    assert response.text == '<div id="root">Application</div>'
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    head = await spa.head(path)
    assert head.status_code == 200 and head.content == b""


async def test_built_assets_and_conditional_requests(spa: httpx.AsyncClient) -> None:
    response = await spa.get("/assets/app-123.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "immutable" in response.headers["cache-control"]
    cached = await spa.get(
        "/assets/app-123.js", headers={"If-None-Match": response.headers["etag"]}
    )
    assert cached.status_code == 304


@pytest.mark.parametrize(
    "path",
    [
        "/api",
        "/api/missing",
        "/assets/missing.js",
        "/unknown",
        "/sites/one/missing",
        "/.env",
        "/index.html",
        "/assets/secret.txt",
        "/assets/%2e%2e/%2e%2e/secret.txt",
        "/assets/%5c..%5csecret.txt",
        "/sites/%2e%2e/login",
    ],
)
async def test_missing_and_unsafe_paths_keep_json_errors(spa: httpx.AsyncClient, path: str) -> None:
    response = await spa.get(path)
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "private sentinel" not in response.text


async def test_spa_mount_preserves_api_docs_and_method_errors(spa: httpx.AsyncClient) -> None:
    assert (await spa.get("/api/me")).status_code == 401
    assert (await spa.get("/healthz")).json() == {"status": "ok"}
    assert (await spa.get("/readyz")).json() == {"status": "ready"}
    assert (await spa.get("/docs")).status_code == 200
    assert "/api/sites" in (await spa.get("/openapi.json")).json()["paths"]
    response = await spa.post("/sites", json={}, headers={"Origin": "http://localhost:8000"})
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
