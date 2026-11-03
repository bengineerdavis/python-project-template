"""Test fixtures for the copier template."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def template_dir(request: pytest.FixtureRequest) -> Path:
    return request.config.rootpath


@pytest.fixture(scope='session')
def mock_answers_required_without_defaults() -> dict[str, Any]:
    """Answers questions deliberately without a default.

    e.g. to force user choice, or because no obvious default exists

    """
    return {
        'project_name': 'Example Project',
        'author_name': 'Ben Davis',
        'author_email': 'ben.davis@example.com',
    }
