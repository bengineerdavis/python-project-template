"""Verify that a lock holding several versions of one package round-trips."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'template' / 'scripts'))

import test_feedback  # noqa: E402


def test_multi_version_entries_are_compared_per_version() -> None:
    native = {
        'package': [
            {
                'name': 'tomli',
                'version': '1.2.3',
                'files': [{'file': 'tomli-1.2.3.whl', 'hash': 'sha256:aaa'}],
            },
            {
                'name': 'tomli',
                'version': '2.0.1',
                'files': [{'file': 'tomli-2.0.1.whl', 'hash': 'sha256:bbb'}],
            },
        ]
    }
    exported = {
        'packages': [
            {
                'name': 'tomli',
                'version': '1.2.3',
                'wheels': [{'name': 'tomli-1.2.3.whl', 'hashes': {'sha256': 'aaa'}}],
            },
            {
                'name': 'tomli',
                'version': '2.0.1',
                'wheels': [{'name': 'tomli-2.0.1.whl', 'hashes': {'sha256': 'bbb'}}],
            },
        ]
    }

    assert test_feedback.locked_artifacts(native) == test_feedback.locked_artifacts(
        exported
    )
