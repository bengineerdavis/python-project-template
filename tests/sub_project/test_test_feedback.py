"""Verify fast feedback through a generated project's public command interface."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def project(
    sub_project_factory: Callable[[dict[str, Any] | None], Path],
    request: pytest.FixtureRequest,
) -> Path:
    installer = request.node.callspec.params['installer']
    return sub_project_factory({'installer': installer})


def run_command(
    project: Path,
    *command: str,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def prepare_project(project: Path) -> None:
    result = run_command(project, 'mise', 'run', 'lock')
    assert result.returncode == 0, output(result)
    result = run_command(project, 'mise', 'run', 'sync')
    assert result.returncode == 0, output(result)


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_public_fast_feedback_contract(project: Path, installer: str) -> None:
    prepare_project(project)
    native_lock = {'uv': 'uv.lock', 'poetry': 'poetry.lock'}.get(
        installer, 'pylock.toml'
    )
    lock_bytes = hashlib.sha256((project / native_lock).read_bytes()).digest()

    result = run_command(project, 'mise', 'run', 'test')
    text = output(result)

    assert result.returncode == 0, text
    assert re.search(r'outcome=passed .*scope=full .*count=3 .*seed=\d+', text)
    assert 'full suite pending' not in text
    assert hashlib.sha256((project / native_lock).read_bytes()).digest() == lock_bytes


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_fast_feedback_uses_prek_without_recursion(
    project: Path, installer: str
) -> None:
    prepare_project(project)

    result = run_command(project, 'mise', 'run', 'test')
    text = output(result)

    assert result.returncode == 0, text
    assert 'test-fast' in text
    assert 'outcome=passed' in text


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_fast_feedback_reports_first_failure_and_seed(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    (project / 'tests/test_feedback_failure.py').write_text(
        'def test_first_failure():\n    assert 1 == 2\n\n'
        'def test_second_failure():\n    assert 2 == 3\n'
    )
    subprocess.run(
        ['git', 'add', 'tests/test_feedback_failure.py'], cwd=project, check=True
    )

    result = run_command(
        project,
        'mise',
        'run',
        'test',
        '--',
        'tests/test_feedback_failure.py::test_first_failure',
    )
    text = output(result)

    assert result.returncode != 0
    assert 'assert 1 == 2' in text
    assert 'test_first_failure' in text
    assert 'test_feedback_failure.py' in text
    assert 'assert 2 == 3' not in text
    assert re.search(r'outcome=failed .*seed=\d+', text)


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_explicit_pytest_selector_and_seed_replay(
    project: Path, installer: str
) -> None:
    prepare_project(project)

    result = run_command(
        project,
        'mise',
        'run',
        'test',
        '--',
        'tests/test_cli.py::test_help_exits_zero',
        '--randomly-seed=2468',
    )
    text = output(result)

    assert result.returncode == 0, text
    assert 'scope=focused' in text
    assert 'count=1' in text
    assert 'seed=2468' in text
    assert 'full suite pending' in text


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_stale_dependency_declarations_do_not_run_tests(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    pyproject = project / 'pyproject.toml'
    pyproject.write_text(pyproject.read_text().replace('pytest>=8', 'pytest>=8.4'))

    result = run_command(project, 'mise', 'run', 'test')
    text = output(result)

    assert result.returncode != 0
    assert 'mise run lock' in text
    assert 'outcome=' not in text


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_flaky_investigation_runs_twice_and_json_agrees(
    project: Path, installer: str
) -> None:
    prepare_project(project)

    result = run_command(project, 'mise', 'run', 'test:flaky', '--json')
    text = output(result)

    assert result.returncode == 0, text
    assert text.count('pytest_exit_code=0') == 2
    assert len(re.findall(r'pytest_seed=\d+', text)) == 2
    json_line = next(line for line in text.splitlines() if line.startswith('{'))
    report = json.loads(json_line)
    assert report['outcome'] == 'passed'
    assert report['scope'] == 'full'
    assert report['count'] == 3
    assert len(report['runs']) == 2
    assert report['runs'][0]['seed'] != report['runs'][1]['seed']


@pytest.mark.parametrize('installer', ['uv'])
def test_flaky_investigation_fails_closed_on_mixed_outcomes(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    counter = project / '.flaky-counter'
    (project / 'tests/test_flaky.py').write_text(
        'from pathlib import Path\n\n'
        'def test_flaky():\n'
        '    counter = Path(".flaky-counter")\n'
        '    previous = int(counter.read_text()) if counter.exists() else 0\n'
        '    counter.write_text(str(previous + 1))\n'
        '    assert previous > 0\n'
    )

    result = run_command(
        project, 'mise', 'run', 'test:flaky', '--', 'tests/test_flaky.py'
    )
    text = output(result)

    assert result.returncode != 0
    assert 'outcome=flaky' in text
    assert text.count('pytest_exit_code=') == 2
    assert counter.read_text() == '2'


@pytest.mark.parametrize('installer', ['uv'])
def test_option_value_does_not_claim_focused_selection(
    project: Path, installer: str
) -> None:
    prepare_project(project)

    result = run_command(
        project, 'mise', 'run', 'test:all', '--', '-p', 'no:cacheprovider'
    )
    text = output(result)

    assert result.returncode == 0, text
    assert 'scope=full' in text
    assert 'full suite pending' not in text


@pytest.mark.parametrize('installer', ['uv'])
def test_manual_prek_exec_preserves_unstaged_test_edits(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    test_file = project / 'tests/test_unstaged_feedback.py'
    test_file.write_text('def test_unstaged_feedback():\n    assert True\n')

    result = run_command(project, 'mise', 'run', 'test')
    text = output(result)

    assert result.returncode == 0, text
    assert 'count=4' in text
    assert 'test-fast' in text


@pytest.mark.parametrize('installer', ['uv'])
def test_git_stages_run_fast_and_full_suite_gates(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    result = run_command(
        project,
        'prek',
        'install',
        '--hook-type',
        'pre-commit',
        '--hook-type',
        'pre-push',
    )
    assert result.returncode == 0, output(result)

    result = run_command(project, 'prek', 'run', 'test-fast', '--stage', 'pre-commit')
    assert result.returncode == 0, output(result)
    result = run_command(project, 'prek', 'run', 'test-all', '--stage', 'pre-push')
    assert result.returncode == 0, output(result)

    (project / 'tests/test_gate_failure.py').write_text(
        'def test_gate_failure():\n    assert False\n'
    )
    subprocess.run(
        ['git', 'add', 'tests/test_gate_failure.py'], cwd=project, check=True
    )
    result = run_command(project, 'prek', 'run', 'test-fast', '--stage', 'pre-commit')
    assert result.returncode != 0
    assert 'test_gate_failure' in output(result)
    result = run_command(project, 'prek', 'run', 'test-all', '--stage', 'pre-push')
    assert result.returncode != 0


@pytest.mark.parametrize('installer', ['uv'])
def test_fresh_checkout_runs_documented_bootstrap(
    project: Path, installer: str
) -> None:
    prepare_project(project)
    subprocess.run(['git', 'add', 'uv.lock', 'pylock.toml'], cwd=project, check=True)
    subprocess.run(
        ['git', 'commit', '-m', 'Lock test dependencies'],
        cwd=project,
        check=True,
        capture_output=True,
    )
    shutil.rmtree(project / '.venv')
    shutil.rmtree(project / '.cache', ignore_errors=True)

    sync = run_command(project, 'mise', 'run', 'sync')
    assert sync.returncode == 0, output(sync)
    result = run_command(project, 'mise', 'run', 'test')

    assert result.returncode == 0, output(result)
    assert 'outcome=passed' in output(result)


@pytest.mark.parametrize('installer', ['uv'])
@pytest.mark.parametrize(
    ('option', 'argument'),
    [('-k', 'test_version'), ('-m', 'not builtin_marker')],
)
def test_selection_options_report_focused_scope(
    project: Path, installer: str, option: str, argument: str
) -> None:
    prepare_project(project)

    result = run_command(project, 'mise', 'run', 'test', '--', option, argument)
    text = output(result)

    assert result.returncode == 0, text
    assert 'scope=focused' in text, text
    assert 'full suite pending' in text


@pytest.mark.parametrize('installer', ['uv'])
@pytest.mark.parametrize('spelling', ['--junitxml', '--junit-xml'])
def test_forwarded_junit_option_does_not_break_the_report(
    project: Path, installer: str, spelling: str
) -> None:
    prepare_project(project)

    result = run_command(project, 'mise', 'run', 'test', '--', spelling, 'result.xml')
    text = output(result)

    assert result.returncode == 0, text
    assert 'pytest_count=0' not in text
    assert 'count=3' in text


@pytest.mark.parametrize('installer', ['uv', 'poetry', 'pip', 'pip-compile'])
def test_ci_bootstrap_preserves_committed_locks(project: Path, installer: str) -> None:
    prepare_project(project)
    lock_names = {
        'uv': ['uv.lock', 'pylock.toml'],
        'poetry': ['poetry.lock', 'pylock.toml'],
        'pip': ['pylock.toml'],
        'pip-compile': ['requirements.txt', 'pylock.toml'],
    }[installer]
    subprocess.run(['git', 'add', *lock_names], cwd=project, check=True)
    subprocess.run(
        ['git', 'commit', '-m', 'Lock test dependencies'],
        cwd=project,
        check=True,
        capture_output=True,
    )
    lock_bytes = {name: (project / name).read_bytes() for name in lock_names}
    shutil.rmtree(project / '.venv')
    (project / '.cache/test-feedback/environment.json').unlink()

    result = run_command(
        project, 'python', 'scripts/test_feedback.py', 'ci', '--installer', installer
    )

    assert result.returncode == 0, output(result)
    assert {name: (project / name).read_bytes() for name in lock_names} == lock_bytes


@pytest.mark.parametrize('installer', ['uv', 'poetry'])
def test_edited_pylock_is_rejected_before_tests(project: Path, installer: str) -> None:
    prepare_project(project)
    pylock = project / 'pylock.toml'
    original = pylock.read_text()
    match = re.search(
        r'^name = "(?P<name>[^"]+)"\nversion = "(?P<version>[^"]+)"',
        original,
        re.MULTILINE,
    )
    assert match, original[:500]
    bumped = '999.0.0'
    pylock.write_text(
        original.replace(
            f'version = "{match.group("version")}"', f'version = "{bumped}"', 1
        )
    )

    result = run_command(project, 'mise', 'run', 'test')
    text = output(result)

    assert result.returncode != 0
    assert 'disagrees with the native lock' in text
    assert 'pytest_exit_code=' not in text
    pylock.write_text(original)
