"""Test fixtures for generating the copier template output."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from copier import run_copy

from tests.helpers import git_save


@pytest.fixture
def sub_project(
    request: pytest.FixtureRequest,
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    mock_answers_required_without_defaults: dict[str, Any],
) -> Path:
    """Create a sub-project by copying the template.

    Can be used directly for default values:

    ```python
        def test_example(sub_project: Path) -> None:
            ...
    ```

    Or with indirect parametrization to pass custom copier data:

    ```python
        @pytest.mark.parametrize(
            ('sub_project','expected'),
            [
                ({'some_option': 'value1'}, 'expected1'),
                ({'some_option': 'value2'}, 'expected2'),
            ],
            indirect=['sub_project'],
        )
        def test_example(sub_project: Path, expected: str) -> None:
            ...
    ```

    """
    data = getattr(request, 'param', {})
    data = mock_answers_required_without_defaults | data
    sub_project = tmp_path_factory.mktemp('sub_project')
    run_copy(
        str(template_dir),
        sub_project,
        vcs_ref='HEAD',
        data=data,
        defaults=True,
        unsafe=True,
    )
    git_save(sub_project)
    return sub_project


@pytest.fixture
def sub_project_factory(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    mock_answers_required_without_defaults: dict[str, Any],
) -> Callable[[dict[str, Any] | None], Path]:
    """Return a factory that creates a sub-project from the template with given data.

    Useful for matrix-style tests with multiple independent parametrize decorators:

    ```python
        @pytest.mark.parametrize('opt_a', ['x', 'y'])
        @pytest.mark.parametrize('opt_b', ['p', 'q'])
        def test_example(sub_project_factory, opt_a, opt_b) -> None:
            sub_project = sub_project_factory({'opt_a': opt_a, 'opt_b': opt_b})
            ...
    ```

    """

    def _factory(data: dict[str, Any] | None = None) -> Path:
        merged = mock_answers_required_without_defaults | (data or {})
        dst = tmp_path_factory.mktemp('sub_project')
        run_copy(
            str(template_dir),
            dst,
            vcs_ref='HEAD',
            data=merged,
            defaults=True,
            unsafe=True,
        )
        git_save(dst)
        return dst

    return _factory
