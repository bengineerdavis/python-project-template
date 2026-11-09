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


def test_equivalent_names_normalize_identically() -> None:
    pairs = [
        ('zope.interface', 'zope-interface'),
        ('a__b', 'a-b'),
        ('a--b', 'a-b'),
        ('Annotated_Doc', 'annotated-doc'),
    ]
    for left, right in pairs:
        assert test_feedback.normalized_name(left) == test_feedback.normalized_name(
            right
        )


def test_option_values_do_not_become_node_ids() -> None:
    # Values of options that are not known flags must not be read as node IDs.
    assert test_feedback.selected_scope(['--import-mode', 'importlib']) == 'full'
    assert test_feedback.selected_scope(['--log-cli-level', 'INFO']) == 'full'
    assert test_feedback.selected_scope(['--tb', 'short', '--color', 'no']) == 'full'
    assert test_feedback.selected_scope(['-p', 'no:cacheprovider']) == 'full'


def test_real_selections_are_reported_as_focused() -> None:
    assert test_feedback.selected_scope(['-k', 'test_version']) == 'focused'
    assert test_feedback.selected_scope(['-ktest_version']) == 'focused'
    assert (
        test_feedback.selected_scope(['tests/test_cli.py::test_version']) == 'focused'
    )
    assert test_feedback.selected_scope(['--deselect=no_such_test']) == 'focused'
