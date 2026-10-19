import argparse
import json
from pathlib import Path

from solar_sites.main import create_app


def export_schema() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI without starting the application")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    schema = export_schema()
    if args.output:
        args.output.write_text(schema)
    else:
        print(schema, end="")


if __name__ == "__main__":
    main()
