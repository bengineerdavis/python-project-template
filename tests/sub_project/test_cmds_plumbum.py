"""Example tests that run shell commands within a generated sub-project.

Uses plumbum
"""

from __future__ import annotations

from pathlib import Path

from plumbum import local
from plumbum.cmd import find, grep


def test_sub_project_has_content(sub_project: Path) -> None:
    """Verify the generated project has files with content."""
    with local.cwd(sub_project):
        (find['.', '-type', 'f'] | grep['.'])()
