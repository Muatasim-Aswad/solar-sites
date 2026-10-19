import http.cookiejar
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
STATE = Path("/data/.smoke.json")
PASSWORD = "Synthetic-smoke-password-123!"
SITE = {
    "clientName": "Smoke client",
    "address": "1 Example Street",
    "latitude": 52.08,
    "longitude": 4.31,
    "peakKwp": 5,
    "roofAreaM2": None,
}


def request(client, path, method="GET", body=None, status=200, csrf=""):
    data = None if body is None else json.dumps(body).encode()
    head = {"Origin": BASE, "Content-Type": "application/json", "X-CSRF-Token": csrf}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=head)
    with client.open(req, timeout=5) as response:
        payload = response.read()
        assert response.status == status, (path, response.status, payload)
        return payload, response.headers


def json_request(client, *args, **kwargs):
    payload, _ = request(client, *args, **kwargs)
    return json.loads(payload)


def check_startup(client):
    assert os.getuid() != 0
    assert json_request(client, "/healthz") == {"status": "ok"}
    assert json_request(client, "/readyz") == {"status": "ready"}
    html, _ = request(client, "/")
    assert b'<div id="root">' in html
    assert request(client, "/sites")[0] == html
    assets = re.findall(rb'(?:src|href)="(/assets/[^\"]+)"', html)
    assert assets, "Built frontend has no asset references"
    for asset in assets:
        content, headers = request(client, asset.decode())
        assert content
        assert "text/html" not in headers["Content-Type"]


def seed_data(client, jar):
    csrf = json_request(
        client,
        "/api/register",
        "POST",
        {"email": "first@example.com", "password": PASSWORD},
        status=201,
    )["csrfToken"]
    site = json_request(client, "/api/sites", "POST", SITE, status=201, csrf=csrf)
    assert site["clientName"] == SITE["clientName"]
    assert json_request(client, "/api/sites/" + site["id"]) == site
    cookie = next(cookie.value for cookie in jar if cookie.name == "solar_session")
    # Carry the expected site and session across container recreation via the volume.
    STATE.write_text(json.dumps({"site": site, "cookie": cookie}))


def check_persistence(client):
    state = json.loads(STATE.read_text())
    client.addheaders = [("Cookie", "solar_session=" + state["cookie"])]
    assert json_request(client, "/api/me")["email"] == "first@example.com"
    assert json_request(client, "/api/sites/" + state["site"]["id"]) == state["site"]
    STATE.unlink()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"seed", "restore"}:
        raise SystemExit("Usage: check.py {seed|restore}")
    phase = sys.argv[1]
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    check_startup(client)
    if phase == "seed":
        seed_data(client, jar)
    else:
        check_persistence(client)
    print("Container checks passed:", phase)


if __name__ == "__main__":
    main()
