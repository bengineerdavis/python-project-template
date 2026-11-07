"""Verify lock and synchronization behavior through public generated-project tasks."""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

INSTALLERS = ['uv', 'poetry', 'pip', 'pip-compile']


def run_task(project: Path, task: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['mise', 'run', task],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def task_script(project: Path, task: str) -> str:
    match = re.search(
        rf'^\[tasks\.{re.escape(task)}\]\n(.*?)(?=^\[tasks\.|\Z)',
        (project / 'mise.toml').read_text(),
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f'missing public task: {task}'
    return match[1]


@pytest.mark.parametrize('installer', INSTALLERS)
def test_sync_installs_without_writing_lock_artifacts(
    sub_project_factory: Callable[[dict[str, Any] | None], Path],
    installer: str,
) -> None:
    project = sub_project_factory({'installer': installer})

    sync = task_script(project, 'sync')
    assert 'pip lock ' not in sync
    assert 'piptools compile ' not in sync
    assert 'poetry lock' not in sync
    assert 'poetry export ' not in sync
    assert 'uv lock' not in sync
    assert 'uv --quiet export ' not in sync

    locked = run_task(project, 'lock')
    assert locked.returncode == 0, locked.stdout + locked.stderr

    artifacts = [
        path
        for name in ('pylock.toml', 'uv.lock', 'poetry.lock', 'requirements.txt')
        if (path := project / name).exists()
    ]
    before = {path: hashlib.sha256(path.read_bytes()).digest() for path in artifacts}
    result = run_task(project, 'sync')

    assert result.returncode == 0, result.stdout + result.stderr
    assert before == {
        path: hashlib.sha256(path.read_bytes()).digest() for path in artifacts
    }
