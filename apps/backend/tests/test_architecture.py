import ast
from importlib.util import resolve_name
from pathlib import Path

import solar_sites


def test_backend_import_boundaries() -> None:
    root = Path(solar_sites.__file__).parent
    graph: dict[str, set[str]] = {}

    def area(parts: tuple[str, ...]) -> str:
        return ".".join(parts[:2]) if parts[0] in {"modules", "infra"} else parts[0]

    for path in root.rglob("*.py"):
        source = path.relative_to(root).with_suffix("").parts
        if source[0] in {"main", "runtime", "openapi", "__init__"}:
            continue
        assert source[0] in {"modules", "infra", "platform", "shared", "config"}, path
        owner = area(source)
        for node in ast.walk(ast.parse(path.read_text())):
            imports: list[str] = []
            if isinstance(node, ast.ImportFrom):
                name = node.module or ""
                if node.level:
                    package = ".".join(("solar_sites", *source[:-1]))
                    name = resolve_name("." * node.level + name, package)
                imports = (
                    [f"{name}.{alias.name}" for alias in node.names]
                    if name in {"solar_sites", "solar_sites.modules", "solar_sites.infra"}
                    else [name]
                )
            elif isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            for name in imports:
                if name is None or not name.startswith("solar_sites."):
                    continue
                target = tuple(name.split(".")[1:])
                dependency = area(target)
                assert target[0] in {"modules", "infra", "platform", "shared", "config"}, (
                    path,
                    name,
                )
                if source[0] in {"infra", "platform", "shared", "config"}:
                    assert target[0] != "modules", (path, name)
                if source[0] == "shared":
                    assert target[0] == "shared", (path, name)
                if source[0] == "config":
                    assert target[0] in {"config", "shared"}, (path, name)
                if source[0] == "infra":
                    assert target[0] in {"infra", "config", "shared"}, (path, name)
                if target[0] == "infra" and owner != dependency:
                    assert len(target) == 2, (path, "Use the integration's public API", name)
                if source[0] == "modules" and target[0] == "modules" and owner != dependency:
                    assert len(target) == 2, (path, "Use the feature's public API", name)
                if source[0] == "modules" and target[0] == "infra":
                    assert source[-1] in {"models", "solar_data_provider_pvgis"}, (path, name)
                if source[0] == "modules" and target[0] == "platform":
                    assert source[-1] in {"routes", "schemas", "dependencies"}, (
                        path,
                        name,
                    )
                if owner != dependency:
                    graph.setdefault(owner, set()).add(dependency)

    def visit(owner: str, stack: frozenset[str]) -> None:
        assert owner not in stack, f"Dependency cycle: {stack} -> {owner}"
        for dependency in graph.get(owner, set()):
            visit(dependency, stack | {owner})

    for owner in graph:
        visit(owner, frozenset())
