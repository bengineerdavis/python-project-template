#!/usr/bin/env python3
"""Run tests from a locked environment and report their outcome and seed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.cache/test-feedback/environment.json'
LOCK_NAMES = ('uv.lock', 'poetry.lock', 'pylock.toml', 'requirements.txt')
INSTALLERS = ('uv', 'poetry', 'pip', 'pip-compile')


def run(
    command: list[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop('VIRTUAL_ENV', None)
    environment['POETRY_VIRTUALENVS_IN_PROJECT'] = 'true'
    environment['POETRY_KEYRING_ENABLED'] = 'false'
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=capture,
        check=False,
    )


def require_success(command: list[str], message: str, *, capture: bool = False) -> str:
    result = run(command, capture=capture)
    if result.returncode != 0:
        if capture:
            sys.stderr.write(result.stderr)
        raise RuntimeError(message)
    return result.stdout


def input_digest() -> str:
    digest = hashlib.sha256()
    for name in ('pyproject.toml', *LOCK_NAMES):
        path = ROOT / name
        digest.update(name.encode())
        digest.update(b'\0')
        if path.exists():
            digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def read_state() -> dict[str, str]:
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_state(**updates: str) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(read_state() | updates, sort_keys=True) + '\n')
    temporary.replace(STATE)


def required_locks(installer: str) -> tuple[str, ...]:
    if installer in {'uv', 'poetry'}:
        return (f'{installer}.lock', 'pylock.toml')
    if installer == 'pip-compile':
        return ('requirements.txt', 'pylock.toml')
    return ('pylock.toml',)


def locked_packages(document: dict[str, object]) -> set[tuple[str, str]]:
    entries = document['packages'] if 'packages' in document else document['package']
    return {
        (str(entry['name']).lower().replace('_', '-'), str(entry['version']))
        for entry in entries
        if 'version' in entry
    }


def _filename(url: str) -> str:
    return PurePosixPath(urlparse(url).path).name


def locked_artifacts(document: dict[str, object]) -> dict[str, set[tuple[str, str]]]:
    """Map each locked package to the artifacts that can satisfy it.

    Artifact pins are the part of a lock that a version comparison cannot see:
    a trojaned wheel keeps its name and version but changes its digest. uv and
    Poetry record the same facts in different shapes, so both are normalised to
    file name plus digest.
    """
    result: dict[str, set[tuple[str, str]]] = {}
    for entry in document.get('packages', []):  # pylock
        if 'version' not in entry:
            continue
        name = str(entry['name']).lower().replace('_', '-')
        files = set()
        sdist = entry.get('sdist') or {}
        for algorithm, value in (sdist.get('hashes') or {}).items():
            filename = _filename(str(sdist.get('url', ''))) or str(
                sdist.get('name', '')
            )
            files.add((filename, f'{algorithm}:{value}'))
        for wheel in entry.get('wheels') or []:
            for algorithm, value in (wheel.get('hashes') or {}).items():
                filename = str(
                    wheel.get('name') or _filename(str(wheel.get('url', '')))
                )
                files.add((filename, f'{algorithm}:{value}'))
        result[name] = files
    for entry in document.get('package', []):  # uv.lock, poetry.lock
        if 'version' not in entry:
            continue
        name = str(entry['name']).lower().replace('_', '-')
        files = set()
        sdist = entry.get('sdist') or {}
        if sdist.get('hash'):
            files.add((_filename(str(sdist.get('url', ''))), str(sdist['hash'])))
        for wheel in entry.get('wheels') or []:
            if wheel.get('hash'):
                files.add((_filename(str(wheel.get('url', ''))), str(wheel['hash'])))
        for item in entry.get('files') or []:
            if item.get('hash'):
                files.add((str(item.get('file', '')), str(item['hash'])))
        result[name] = files
    return result


def check_export_matches_native_lock(installer: str) -> None:
    """Fail when pylock.toml disagrees with the native lock it was exported from.

    Native lock validation cannot see edits to pylock.toml, and pip has no native
    validation at all, so compare the resolved packages and their artifact
    digests offline.
    """
    if installer not in {'uv', 'poetry'}:
        return
    pylock = tomllib.loads((ROOT / 'pylock.toml').read_text())
    native = tomllib.loads((ROOT / f'{installer}.lock').read_text())
    exported = locked_packages(pylock)
    native_packages = locked_packages(native)
    # pylock records the project itself as an editable entry without a version,
    # so it can only be checked in the direction it describes.
    if exported - native_packages:
        raise RuntimeError(
            'pylock.toml disagrees with the native lock; run mise run lock'
        )
    project_name = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project'][
        'name'
    ]
    own = {
        package
        for package in native_packages
        if package[0] == project_name.lower().replace('_', '-')
    }
    if native_packages - own - exported:
        raise RuntimeError(
            'pylock.toml disagrees with the native lock; run mise run lock'
        )
    exported_artifacts = locked_artifacts(pylock)
    native_artifacts = locked_artifacts(native)
    for name, files in exported_artifacts.items():
        expected = native_artifacts.get(name)
        if expected is not None and files != expected:
            raise RuntimeError(
                'pylock.toml artifacts disagree with the native lock; run mise run lock'
            )


def check_locks(installer: str) -> None:
    missing = [
        name for name in required_locks(installer) if not (ROOT / name).is_file()
    ]
    if missing:
        raise RuntimeError(f'missing {", ".join(missing)}; run mise run lock')
    if installer == 'uv':
        command = ['uv', 'lock', '--check']
    elif installer == 'poetry':
        command = ['poetry', 'check', '--lock']
    else:
        command = None
    if command:
        require_success(command, 'stale native lock; run mise run lock', capture=True)
    check_export_matches_native_lock(installer)


def create_venv(path: Path, packages: list[str]) -> Path:
    python = path / 'bin/python'
    if not python.exists():
        require_success(
            [sys.executable, '-m', 'venv', str(path)], 'could not create environment'
        )
    require_success(
        [str(python), '-m', 'pip', 'install', '--upgrade', *packages],
        'could not install tool',
    )
    return python


def sync_environment(installer: str) -> None:
    if installer == 'uv':
        require_success(
            ['uv', 'sync', '--all-groups', '--locked'], 'synchronization failed'
        )
    elif installer == 'poetry':
        interpreter = ROOT / '.venv/bin/python'
        if not interpreter.exists():
            require_success(
                [sys.executable, '-m', 'venv', '.venv'], 'could not create environment'
            )
        require_success(
            ['poetry', 'env', 'use', str(interpreter)], 'environment selection failed'
        )
        require_success(['poetry', 'sync'], 'synchronization failed')
    else:
        python = create_venv(ROOT / '.venv', ['pip>=26.1'])
        # Only pip records the project itself as an unhashable editable entry.
        # pip-compile locks are fully hashed, so keep hash verification enforced.
        hash_flags = ['--no-require-hashes'] if installer == 'pip' else []
        require_success(
            [
                str(python),
                '-m',
                'pip',
                'install',
                '--no-deps',
                *hash_flags,
                '--requirement',
                'pylock.toml',
            ],
            'locked dependency installation failed',
        )
        require_success(
            [str(python), '-m', 'pip', 'install', '--no-deps', '--editable', '.'],
            'project installation failed',
        )
    if installer == 'poetry':
        require_success(
            ['poetry', 'run', 'python', '-c', 'import pytest'],
            'the synchronized environment cannot import pytest',
        )
    write_state(sync_digest=input_digest())


def ensure_lock_digest(installer: str) -> str:
    """Return the recorded lock digest, adopting committed locks on a fresh clone.

    The state file is local and gitignored, so a clone carrying valid committed
    locks has no recorded digest. Validating those locks and adopting their
    digest is what lets the documented install/sync sequence run without a
    redundant `mise run lock`.
    """
    digest = input_digest()
    state = read_state()
    recorded = state.get('lock_digest')
    if not recorded:
        check_locks(installer)
        if installer in {'pip', 'pip-compile'}:
            # check_locks has no content validation for these installers, so a
            # stale committed lock would otherwise become the trusted digest.
            verify_pip_lock(installer)
        write_state(lock_digest=digest)
        return digest
    if recorded != digest:
        raise RuntimeError('dependency inputs changed; run mise run lock')
    return digest


def prepare_environment(installer: str) -> None:
    check_locks(installer)
    digest = ensure_lock_digest(installer)
    if read_state().get('sync_digest') != digest:
        sync_environment(installer)


def normalized_pylock(path: Path) -> object:
    """Return pylock dependency content without generator metadata.

    `created-by` and wheel URLs record which tool and index produced the lock,
    so a lock regenerated by an equivalent pip version is not stale.
    """
    document = tomllib.loads(path.read_text())
    packages = []
    for entry in document.get('packages', []):
        wheels = sorted(
            (
                wheel.get('name'),
                wheel.get('url'),
                tuple(sorted(wheel.get('hashes', {}).items())),
            )
            for wheel in entry.get('wheels', [])
        )
        sdist = entry.get('sdist') or {}
        packages.append(
            {
                'name': entry.get('name'),
                'version': entry.get('version'),
                'marker': entry.get('marker'),
                'wheels': wheels,
                'sdist': (
                    sdist.get('name') or sdist.get('url'),
                    tuple(sorted(sdist.get('hashes', {}).items())),
                )
                if sdist
                else None,
            }
        )
    return sorted(packages, key=lambda package: str(package['name']))


VERIFIER_PACKAGES = ['packaging==26.3']


def pinned_versions(requirements: Path) -> dict[str, str]:
    pins = {}
    for line in requirements.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line or line.startswith('-') or '==' not in line:
            continue
        name, _, version = line.partition('==')
        pins[name.strip().lower().replace('_', '-')] = version.strip()
    return pins


def verify_pip_lock(installer: str) -> None:
    """Verify a pip-generated lock without resolving dependencies again.

    Re-resolving against the live index made an unchanged commit fail whenever
    an unrelated release appeared, so the declarations are checked against the
    committed lock instead. Only the verifier tool is fetched, pinned exactly.
    """
    with tempfile.TemporaryDirectory(prefix='.verify-lock-', dir=ROOT) as directory:
        work = Path(directory)
        python = create_venv(work / 'venv', VERIFIER_PACKAGES)
        result = run(
            [
                str(python),
                str(ROOT / 'scripts/verify_lock_declarations.py'),
                'pyproject.toml',
                'pylock.toml',
            ],
            capture=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                'pylock.toml does not satisfy pyproject.toml; run mise run lock'
            )
        if installer == 'pip-compile':
            # pylock.toml can already contain a newly declared dependency as a
            # transitive one, so requirements.txt must satisfy the declarations
            # too. Comparing names offline keeps verification stable.
            declarations = run(
                [
                    str(python),
                    '-c',
                    (
                        'import sys;'
                        "sys.path.insert(0, 'scripts');"
                        'import tomllib,json;'
                        'from verify_lock_declarations import declared_requirements;'
                        'print(json.dumps([r.name for r in declared_requirements('
                        "tomllib.load(open('pyproject.toml','rb')))]))"
                    ),
                ],
                capture=True,
            )
            if declarations.returncode != 0:
                raise RuntimeError('could not read declared dependencies')
            pins = pinned_versions(ROOT / 'requirements.txt')
            missing = [
                name.lower().replace('_', '-')
                for name in json.loads(declarations.stdout)
                if name.lower().replace('_', '-') not in pins
            ]
            if missing:
                raise RuntimeError('requirements.txt is stale; run mise run lock')
            locked = normalized_pylock(ROOT / 'pylock.toml')
            versions = {
                str(package['name']).lower().replace('_', '-'): package['version']
                for package in locked
            }
            stale = [
                name for name, version in pins.items() if versions.get(name) != version
            ]
            if stale:
                raise RuntimeError(
                    'requirements.txt disagrees with pylock.toml; run mise run lock'
                )


def bootstrap_ci(installer: str) -> None:
    check_locks(installer)
    if installer in {'pip', 'pip-compile'}:
        verify_pip_lock(installer)
    write_state(lock_digest=input_digest())
    sync_environment(installer)


def pytest_command(installer: str) -> list[str]:
    if installer == 'uv':
        return ['uv', 'run', '--locked', '--no-sync', 'python', '-m', 'pytest']
    if installer == 'poetry':
        return ['poetry', 'run', 'python', '-m', 'pytest']
    python = ROOT / '.venv/bin/python'
    if not python.exists():
        raise RuntimeError('the project environment is missing; run mise run sync')
    return [str(python), '-m', 'pytest']


def seed_arguments(arguments: list[str]) -> tuple[list[str], list[int]]:
    remaining = []
    seeds = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == '--randomly-seed':
            if index + 1 == len(arguments):
                raise RuntimeError('--randomly-seed requires an integer')
            value = arguments[index + 1]
            index += 2
        elif argument.startswith('--randomly-seed='):
            value = argument.partition('=')[2]
            index += 1
        else:
            remaining.append(argument)
            index += 1
            continue
        try:
            seed = int(value, 0)
        except ValueError as error:
            raise RuntimeError('--randomly-seed requires an integer') from error
        if not 0 <= seed <= 2**32 - 1:
            raise RuntimeError('--randomly-seed must fit in 32 bits')
        seeds.append(seed)
    return remaining, seeds


def run_pytest(
    installer: str,
    mode: str,
    arguments: list[str],
    seed: int,
    machine_readable: bool = False,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix='test-feedback-') as directory:
        report_path = Path(directory) / 'result.xml'
        command = pytest_command(installer)
        if mode == 'fast':
            command.extend(['--maxfail=1', '--tb=short', '-rN', '--no-header', '-q'])
        command.extend(
            [f'--randomly-seed={seed}', f'--junitxml={report_path}', *arguments]
        )
        started = time.monotonic()
        result = run(command, capture=True)
        diagnostic = sys.stderr if machine_readable else sys.stdout
        diagnostic.write(result.stdout)
        sys.stderr.write(result.stderr)
        diagnostic.flush()
        sys.stderr.flush()
        count = skipped = failures = 0
        if report_path.exists():
            cases = list(ET.parse(report_path).getroot().iter('testcase'))
            skipped = sum(case.find('skipped') is not None for case in cases)
            count = len(cases) - skipped
            failures = sum(
                case.find('failure') is not None or case.find('error') is not None
                for case in cases
            )
        if result.returncode == 7 or (result.returncode == 0 and failures):
            outcome = 'flaky'
        else:
            outcome = 'passed' if result.returncode == 0 else 'failed'
        print(
            f'pytest_exit_code={result.returncode} pytest_seed={seed} '
            f'pytest_count={count} pytest_skipped={skipped}',
            file=sys.stderr if machine_readable else sys.stdout,
            flush=True,
        )
        return {
            'seed': seed,
            'count': count,
            'skipped': skipped,
            'outcome': outcome,
            'pytest_exit_code': result.returncode,
            'duration_ms': round((time.monotonic() - started) * 1000),
        }


JUNIT_OPTIONS = ('--junitxml', '--junit-xml')
SELECTION_OPTIONS = (
    '-k',
    '-m',
    '--lf',
    '--last-failed',
    '--ff',
    '--failed-first',
    '--ignore',
    '--ignore-glob',
    '--deselect',
    '--maxfail',
    '-x',
    '--exitfirst',
)
VALUE_OPTIONS = (
    '-k',
    '-m',
    '-p',
    '-c',
    '-o',
    '--rootdir',
    '--confcutdir',
    '--basetemp',
    '--ignore',
    '--ignore-glob',
    '--deselect',
    '--maxfail',
    '--last-failed-no-failures',
    '--junit-prefix',
    '--max-warnings',
    '--tb',
    '--color',
    '--durations',
    '--log-level',
    '--capture',
    '--runxfail',
)


def reject_reserved_options(arguments: list[str]) -> list[str]:
    """Drop options that would collide with the runner's own reporting.

    A forwarded --junitxml replaces the internal report path, leaving the
    runner unable to count tests even when the suite passes.
    """
    kept = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in JUNIT_OPTIONS:
            index += 2
            continue
        if any(argument.startswith(f'{option}=') for option in JUNIT_OPTIONS):
            index += 1
            continue
        kept.append(argument)
        index += 1
    return kept


def selected_scope(arguments: list[str]) -> str:
    """Report whether the run covers the whole suite or a selection.

    Selection arrives as pytest options or as explicit node IDs, so it is
    decided from the arguments rather than by spending a second pytest start
    on collection.
    """
    previous = ''
    for argument in arguments:
        option = argument.partition('=')[0]
        if option in SELECTION_OPTIONS:
            return 'focused'
        # Attached forms such as -ktest_version or -m "not slow" select tests too.
        if len(argument) > 2 and argument[:2] in {'-k', '-m'}:
            return 'focused'
        if not argument.startswith('-') and previous not in VALUE_OPTIONS:
            return 'focused'
        previous = argument
    return 'full'


def exit_code(outcome: str, runs: list[dict[str, object]]) -> int:
    """Preserve the raw pytest status so callers can tell failures apart.

    A mixed flaky result has no pytest status of its own, so it reports 7;
    a setup error keeps 2. Everything else passes the first run's status on.
    """
    if outcome == 'passed':
        return 0
    if outcome == 'flaky':
        return 7
    return int(runs[0]['pytest_exit_code']) or 1


def run_tests(
    installer: str, mode: str, arguments: list[str], json_output: bool
) -> int:
    prepare_environment(installer)
    arguments = reject_reserved_options(arguments)
    arguments, seeds = seed_arguments(arguments)
    if not seeds:
        seeds = [secrets.randbits(32)]
    if mode == 'flaky' and len(seeds) == 1:
        seeds.append(secrets.randbits(32))
    runs = [run_pytest(installer, mode, arguments, seed, json_output) for seed in seeds]
    outcomes = {run['outcome'] for run in runs}
    if outcomes == {'passed'}:
        outcome = 'passed'
    elif 'flaky' in outcomes or len(outcomes) > 1:
        outcome = 'flaky'
    else:
        outcome = 'failed'
    scope = selected_scope(arguments)
    report = {
        'schema_version': 1,
        'command': mode,
        'outcome': outcome,
        'scope': scope,
        'count': runs[0]['count'],
        'total_count': sum(int(run['count']) for run in runs),
        'runs': runs,
        'exit_code': exit_code(outcome, runs),
    }
    seed_text = ','.join(str(run['seed']) for run in runs)
    pending = (
        '; full suite pending' if scope == 'focused' and outcome == 'passed' else ''
    )
    human = f'outcome={outcome} scope={scope} count={report["total_count"]} seed={seed_text}{pending}'
    # The JSON document is the only thing on stdout when it is requested.
    print(human, file=sys.stderr if json_output else sys.stdout, flush=True)
    if json_output:
        print(json.dumps(report, sort_keys=True), flush=True)
    return int(report['exit_code'])


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer', choices=INSTALLERS, required=True)
    parser.add_argument(
        'mode',
        choices=[
            'fast',
            'full',
            'flaky',
            'sync',
            'ready',
            'ci',
            'record-lock',
            'record-sync',
        ],
    )
    parser.add_argument('--json', action='store_true', dest='json_output')
    arguments = sys.argv[1:]
    if arguments[:1] == ['--']:
        arguments = arguments[1:]
    if '--' in arguments:
        separator = arguments.index('--')
        options, pytest_arguments = arguments[:separator], arguments[separator + 1 :]
        parsed = parser.parse_args(options)
    else:
        parsed, pytest_arguments = parser.parse_known_args(arguments)
    parsed.pytest_args = pytest_arguments
    return parsed


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.mode == 'record-lock':
            write_state(lock_digest=input_digest())
            return 0
        if arguments.mode == 'record-sync':
            ensure_lock_digest(arguments.installer)
            write_state(sync_digest=input_digest())
            return 0
        if arguments.mode == 'sync':
            # Validation and lock adoption happen before any installation, so a
            # stale or tampered lock cannot install unverified artifacts first.
            ensure_lock_digest(arguments.installer)
            sync_environment(arguments.installer)
            return 0
        if arguments.mode == 'ready':
            prepare_environment(arguments.installer)
            return 0
        if arguments.mode == 'ci':
            bootstrap_ci(arguments.installer)
            return 0
        return run_tests(
            arguments.installer,
            arguments.mode,
            arguments.pytest_args,
            arguments.json_output,
        )
    except RuntimeError as error:
        print(f'test setup: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
