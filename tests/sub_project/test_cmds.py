"""Example tests that run shell commands within a generated sub-project.

Uses python builtin functionality
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_sub_project_has_content(sub_project: Path) -> None:
    """Verify the generated project has files with content."""
    subprocess.run(
        'find . -type f | grep .',
        cwd=sub_project,
        shell=True,
        check=True,
    )
