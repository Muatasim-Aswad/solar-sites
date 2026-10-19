from pathlib import Path

from solar_sites.openapi import export_schema

schema = Path("apps/backend/openapi.json")
if schema.read_text() != export_schema():
    raise SystemExit("Backend OpenAPI drift: run mise run api:generate")
print("Backend OpenAPI matches source")
