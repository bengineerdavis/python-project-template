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
    runner = (project / 'scripts/test_feedback.py').read_text()
    readme = (project / 'README.md').read_text()
    assert 'pylock.toml' in mise
    assert 'pylock.toml' in runner
    assert 'python scripts/test_feedback.py ci' in workflow
    assert 'python scripts/test_feedback.py full' in workflow
    assert 'pylock.toml' in readme
    assert 'git init' in readme
    assert f'python scripts/test_feedback.py fast --installer {installer}' in mise
    assert f'python scripts/test_feedback.py full --installer {installer}' in mise
    assert f'python scripts/test_feedback.py flaky --installer {installer}' in mise
    assert 'pytest-randomly>=5' in dev_dependencies
    assert 'prek>=0.5' in dev_dependencies

    assert f'python scripts/test_feedback.py sync --installer {installer}' in mise

    if installer == 'uv':
        assert 'uv --quiet export --all-groups' in mise
        assert '--all-groups' in runner
        assert '--locked' in runner
        assert 'astral-sh/setup-uv@v5' in workflow
    elif installer == 'poetry':
        assert 'poetry export --all-groups' in mise
        assert 'poetry check --lock' in mise
        assert 'env' in runner
        assert 'use' in runner
        assert 'sync' in runner
        assert 'poetry-plugin-export = ">=1.10"' in pyproject_text
    elif installer == 'pip':
        assert 'pip lock -e . --group dev' in mise
        assert 'actions/setup-python@v5' in workflow
    else:
        assert 'piptools compile --extra dev' in mise
        assert 'pip' in runner
        assert 'lock' in runner
        assert 'verify_lock_declarations.py' in runner


def test_test_feedback_gates_are_declared_and_installed(
    sub_project_factory: Callable[[dict[str, Any] | None], Path],
) -> None:
    project = sub_project_factory({'installer': 'uv'})

    mise = (project / 'mise.toml').read_text()
    prek_config = (project / 'prek.toml').read_text()

    assert 'prek = "latest"' in mise
    assert '[tasks.install]' in mise
    assert 'prek install --hook-type pre-commit --hook-type pre-push' in mise
    assert 'default_install_hook_types = ["pre-commit", "pre-push"]' in prek_config


def test_clean_removes_the_sync_state_with_the_environment(
    sub_project_factory: Callable[[dict[str, Any] | None], Path],
) -> None:
    """A clean that keeps the state file would make the next run skip syncing."""
    project = sub_project_factory({'installer': 'uv'})

    clean = tomllib.loads((project / 'mise.toml').read_text())['tasks']['clean']

    assert '.venv' in clean['run']
    assert '.cache/test-feedback' in clean['run']
