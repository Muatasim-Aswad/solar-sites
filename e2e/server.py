import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from solar_sites.config import Settings
from solar_sites.main import create_app


def solar_data(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/v5_3/seriescalc":
        start = datetime(2023, 1, 1)
        return httpx.Response(
            200,
            json={
                "outputs": {
                    "hourly": [
                        {
                            "time": (start + timedelta(hours=hour)).strftime(
                                "%Y%m%d:%H%M"
                            ),
                            "P": 2000 if hour % 2 == 0 else 0,
                        }
                        for hour in range(8760)
                    ]
                }
            },
        )
    if request.url.path != "/api/v5_3/PVcalc":
        raise AssertionError(f"Unexpected PVGIS request: {request.url.path}")
    return httpx.Response(
        200,
        json={
            "outputs": {
                "monthly": {
                    "fixed": [{"month": month, "E_m": 730} for month in range(1, 13)]
                },
                "totals": {"fixed": {"E_y": 8760}},
            }
        },
    )


if __name__ == "__main__":
    port = int(os.environ["E2E_PORT"])
    with TemporaryDirectory(prefix="solar-sites-e2e-") as directory:
        settings = Settings(
            database_path=Path(directory) / "database.sqlite3",
            frontend_path=Path(__file__).resolve().parents[1] / "apps/frontend/dist",
            allowed_hosts=["127.0.0.1"],
            allowed_origins=[f"http://127.0.0.1:{port}"],
            cookie_secure=False,
            pvgis_year=2023,
        )
        app = create_app(settings, pvgis_transport=httpx.MockTransport(solar_data))
        uvicorn.run(app, host="127.0.0.1", port=port)
