# Solar sites

A web app for solar advisors to manage client sites, view monthly and yearly PVGIS production estimates, and compare solar self-consumption with and without a home battery. Each advisor sees only their own sites.

## Run with Docker

With Docker running and port 8000 free, run from the repository root:

```sh
docker build -t solar .
docker run -p 8000:8000 solar
```

Open [localhost:8000](http://localhost:8000), register an account and add a site. Enter annual electricity use and battery capacity to compare self-consumption. Internet access is needed for the build and PVGIS estimates; no API key is required.

For a quick example, use latitude `52.08`, longitude `4.31` and panel capacity `5 kWp`, then compare a `5 kWh` battery with annual electricity use of `3500 kWh`.

The running app also provides [Swagger UI](http://localhost:8000/docs) and [OpenAPI JSON](http://localhost:8000/openapi.json).

## Decisions and assumptions

- **Backend:** FastAPI supports async requests so waiting for network calls lets other requests progress. Pydantic provides validation and generated OpenAPI schemas. SQLite keeps the Docker app self-contained; SQLAlchemy and Alembic manage persistence and migrations.
- **Frontend and tooling:** Vite+ brings development, builds and checks together; mise pins tools, while uv and pnpm lock dependencies. Frontend uses React and Typescript and its API types are generated from the backend to keep the two in sync.
- **Consumption:** The advisor's annual electricity use is spread equally across every hour. This gives a reproducible baseline without requiring a household load profile, but misses real demand patterns.
- **Battery:** Starts empty, stores surplus solar and supplies later deficits, with 100% efficiency and no charging/discharging power limit. Energy left at year-end is excluded from self-use. This is an indicative energy comparison.
- **PVGIS:** Uses v5_3, 14% system loss and hourly simulation year 2023. Other optional settings use PVGIS defaults. Monthly/yearly estimates and the hourly battery simulation can differ.
- **Account safety:** Server-side sessions use an HttpOnly cookie for authentication. CSRF protection secures authenticated writes, and ownership checks keep each advisor's sites private.

See [architecture and implementation decisions](docs/architecture.md) for the engineering rationale and [the energy model](docs/energy-model.md) for assumptions, calculations and limitations.

## Structure

```text
.
├── apps/
│   ├── backend/
│   │   ├── src/solar_sites/
│   │   │   ├── infra/
│   │   │   │   ├── database/         # Connections and migrations
│   │   │   │   └── pvgis/            # HTTP client and response parsing
│   │   │   ├── modules/
│   │   │   │   ├── auth/             # Accounts and sessions
│   │   │   │   ├── energy/           # Production and battery calculations
│   │   │   │   └── sites/            # Advisor-owned site management
│   │   │   ├── platform/             # HTTP mechanisms and dependency providers
│   │   │   └── shared/               # Transport-independent application errors
│   │   ├── tests/                    # Calculation and API tests
│   │   └── openapi.json              # Generated API contract
│   └── frontend/src/
│       ├── app/                      # Routing, session setup and shell
│       ├── features/                 # Pages, components and feature queries
│       ├── infra/                    # API clients and generated types
│       └── shared/                   # Reusable UI and formatting
├── docs/                             # Rationale and model details
├── e2e/                              # Browser workflows and test server
├── scripts/                          # Verification and container checks
├── .github/workflows/                # CI checks
├── Dockerfile                        # Builds and serves both apps
└── mise.toml                         # Tools and development tasks
```

## Develop locally

Install [mise](https://mise.jdx.dev/). For first setup, run from the repository root:

```sh
mise trust mise.toml
mise install --locked
mise run setup
cp .env.example .env
```

Start from separate terminals in the repository root then open [localhost:5173](http://localhost:5173). The frontend proxies API requests to the backend on port 8000.

```sh
mise run dev:backend
mise run dev:frontend
```

## Checks

| Command | Purpose |
| --- | --- |
| `mise run check` | Check formatting and lint; also runs before commits when `.githooks` is enabled. |
| `mise run test` | Run backend, frontend unit and browser tests; browser setup builds the frontend. |
| `mise run verify` | Combine `check` and `test` with type and generated API checks. |
| `mise run container-smoke` | With Docker running, check the packaged app and persistence across restarts. |
| `mise run api:generate` | Regenerate OpenAPI and frontend types after API changes. |

`mise run setup` installs dependencies and Chromium for browser tests; rerun it after dependency changes.

Browser tests start their own app on port 18000 with a temporary database and fixed PVGIS responses. Keep that port free.
