"""Tests for the copier template."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from copier import run_copy, run_update

from tests.helpers import git_save, is_git_repo_dirty


def test_copy_default(
    template_dir: Path,
    tmp_path: Path,
    mock_answers_required_without_defaults: dict[str, Any],
) -> None:
    worker = run_copy(
        str(template_dir),
        tmp_path,
        vcs_ref='HEAD',
        defaults=True,
        data=mock_answers_required_without_defaults,
        unsafe=True,  # set to False if unsafe features not needed for template
    )
    assert (tmp_path / worker.answers_relpath).exists()


@pytest.mark.skipif(is_git_repo_dirty(), reason='Fail on dirty repo')
def test_update_default(
    template_dir: Path,
    tmp_path: Path,
    mock_answers_required_without_defaults: dict[str, Any],
) -> None:
    worker = run_copy(
        str(template_dir),
        tmp_path,
        defaults=True,
        data=mock_answers_required_without_defaults,
        unsafe=True,
    )
    git_save(tmp_path)
    run_update(
        tmp_path,
        vcs_ref='HEAD',
        defaults=True,
        overwrite=True,  # The default when run via CLI
        answers_file=worker.answers_relpath,
        unsafe=True,  # set to False if unsafe features not needed for template
    )
    assert (tmp_path / worker.answers_relpath).exists()
