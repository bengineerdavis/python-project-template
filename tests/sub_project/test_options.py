# Copyright (c) 2026 Ben Davis
"""Tests for type-checker and installer template options."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize('type_checker', ['pyrefly', 'mypy'])
@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_tooling_options(
    sub_project_factory: Callable[[dict[str, Any] | None], Path],
    installer: str,
    type_checker: str,
) -> None:
    project = sub_project_factory(
        {'installer': installer, 'type_checker': type_checker},
    )

    pyproject_text = (project / 'pyproject.toml').read_text()
    pyproject = tomllib.loads(pyproject_text)
    if installer == 'pip-compile':
        dev_dependencies = pyproject['project']['optional-dependencies']['dev']
        assert 'dependency-groups' not in pyproject
    else:
        dev_dependencies = pyproject['dependency-groups']['dev']
    assert 'pytest>=8' in dev_dependencies
    assert 'ruff>=0.17' in dev_dependencies
    assert f'{type_checker}>=' in ' '.join(dev_dependencies)
    other_checker = 'mypy' if type_checker == 'pyrefly' else 'pyrefly'
    assert other_checker not in pyproject_text
    assert type_checker in pyproject['tool']

    mise = (project / 'mise.toml').read_text()
    workflow = (project / '.github/workflows/test.yml').read_text()
    readme = (project / 'README.md').read_text()
    assert 'pylock.toml' in mise
    assert 'pylock.toml' in workflow
    assert 'pylock.toml' in readme
    assert f'run = "{run_prefix(installer)} pytest"' in mise

    if installer == 'uv':
        assert 'uv --quiet export --all-groups' in mise
        assert 'astral-sh/setup-uv@v5' in workflow
    elif installer == 'poetry':
        assert 'poetry export --all-groups' in mise
        assert 'poetry-plugin-export = ">=1.10"' in pyproject_text
    elif installer == 'pip':
        assert 'pip lock -e . --group dev' in mise
        assert 'actions/setup-python@v5' in workflow
    else:
        assert 'piptools compile --extra dev' in mise
        assert 'pip lock --requirement requirements.txt' in workflow


def run_prefix(installer: str) -> str:
    if installer == 'uv':
        return 'uv run'
    if installer == 'poetry':
        return 'poetry run'
    return '.venv/bin/python -m'
