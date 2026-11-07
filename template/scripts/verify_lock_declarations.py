"""Check that a lock satisfies the dependency declarations in pyproject.toml.

Run with an interpreter that provides `packaging`. This reads two files and
resolves nothing, so verifying an unchanged commit stays stable as new
releases appear upstream.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def declared_requirements(pyproject: dict) -> list[Requirement]:
    project = pyproject.get("project", {})
    declarations = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        declarations.extend(group)
    for group in pyproject.get("dependency-groups", {}).values():
        declarations.extend(item for item in group if isinstance(item, str))

    poetry = pyproject.get("tool", {}).get("poetry", {})
    for section in ("dependencies", "dev-dependencies"):
        for name, spec in poetry.get(section, {}).items():
            if name != "python" and isinstance(spec, str):
                declarations.append(f"{name}{spec}")
    for group in poetry.get("group", {}).values():
        for name, spec in group.get("dependencies", {}).items():
            if isinstance(spec, str):
                declarations.append(f"{name}{spec}")
    return [Requirement(item) for item in declarations]


def locked_versions(pylock: dict) -> dict[str, set[str]]:
    versions: dict[str, set[str]] = {}
    for entry in pylock.get("packages", []):
        version = entry.get("version")
        if version:
            versions.setdefault(canonicalize_name(str(entry["name"])), set()).add(str(version))
    return versions


def failures(pyproject_path: Path, pylock_path: Path) -> list[str]:
    pyproject = tomllib.loads(pyproject_path.read_text())
    locked = locked_versions(tomllib.loads(pylock_path.read_text()))
    problems = []
    for requirement in declared_requirements(pyproject):
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        name = canonicalize_name(requirement.name)
        candidates = locked.get(name)
        if not candidates:
            problems.append(f"{requirement} is declared but absent from the lock")
        elif not any(
            requirement.specifier.contains(candidate, prereleases=True) for candidate in candidates
        ):
            problems.append(
                f"{requirement} is declared but the lock has {', '.join(sorted(candidates))}"
            )
    return problems


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: verify_lock_declarations.py pyproject.toml pylock.toml",
            file=sys.stderr,
        )
        return 2
    try:
        problems = failures(Path(sys.argv[1]), Path(sys.argv[2]))
    except (ValueError, tomllib.TOMLDecodeError) as error:
        print(f"could not verify lock declarations: {error}", file=sys.stderr)
        return 2
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
