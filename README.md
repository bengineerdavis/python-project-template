# python-project-template

Base copier template for modern Python CLI projects. Stamped underneath
the agentic layer
([agentic-project-template](https://github.com/bengineerdavis/agentic-project-template)),
which composes it:

    agentic-project-template new <dst> --base /path/to/python-project-template

This template owns language, build, test, and lint concerns. The agentic
layer owns review loops (roborev fast loop, review-deep slow loop), task
management (backlog-py), agent wiring (dotagents), and structure enforcement
(alint + tombi). Neither crosses into the other's concerns.

This repository derives its template-development tooling and test harness from
[copier-template-copier-template](https://github.com/bengineerdavis/copier-template-copier-template).
The derivation is recorded in `.copier-answers.copier-template.yml`, so future
meta-template improvements can be inherited with `mise run update-template`.

## What it stamps

- `pyproject.toml` — hatchling build, `src/` layout, typer CLI, development
  dependencies, and ruff + pyrefly/mypy + pytest config. Distribution name,
  import name, and console-script name can all differ (`package_name`,
  `project_slug`, `cli_name` — e.g. `redge-cli` / `redge` / `redge`).
- `mise.toml` — python plus the selected uv/Poetry/pip/pip-compile tooling;
  lock, sync, test, lint, format, format-check, type-check, and quality tasks.
  Minimal and conventionally shaped so the agentic layer's TOML deep-merge
  (and aboyeur) can extend it.
- `prek.toml` — ruff lint + format hooks only. No generic builtins: in
  layer-stamped projects alint owns whitespace/newline/merge-marker checks
  (no-overlap rule).
- `src/<slug>/` + `tests/` — working typer CLI with a sample command and
  passing tests.
- `.github/workflows/test.yml` — installer-specific CI (lint, format, types, tests).
- `LICENSE` — MIT or FSL-1.1-MIT (Fair Source; converts to MIT after two
  years).
- `README.md`, `CHANGELOG.md`, `AGENTS.md` (project map; the layer appends
  its managed section).

Generated projects use `.copier-answers.python-project-template.yml` for this
template's answers. The separate answers file lets the agentic layer stamp on
top without taking ownership of this template's update metadata.

## Tooling and lockfile policy

Pyrefly is the default type checker; mypy is optional. uv is the default
installer, with Poetry, pip, and pip-compile alternatives. Every choice has a
`pylock.toml` workflow:

- uv and Poetry keep their native source locks and export `pylock.toml`.
- pip writes `pylock.toml` directly with its experimental `pip lock` command.
- pip-compile writes `requirements.txt`, then `pip lock` converts that
  intermediate to `pylock.toml`.

A strict native-`pylock.toml`-only policy was rejected because uv and Poetry
cannot replace their native locks and pip-tools has no native PEP 751 output.
Allowing a requirements-file-only pip-compile variant was also rejected:
`requirements.txt` is only an intermediate, never the final lock format.

## Install Copier

```bash
uv tool install copier
# or
pipx install copier
# or
brew install copier
```

## Usage

### Create a new project

```bash
copier copy <template-url> /path/to/new/project
```

For non-interactive usage (scripts, CI, AI agents), see `copier copy --help` for the `--defaults` and `--data` flags.

### Update an existing project

```bash
cd /path/to/your/project
copier update --answers-file .copier-answers.python-project-template.yml
```

For non-interactive updates, use `--skip-answered` to reuse all existing answers without prompting.

## Development

Prerequisites: [uv](https://docs.astral.sh/uv/) and [mise](https://mise.jdx.dev/).

Run `mise tasks` to see available commands (mise is the task runner). See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development guide.

Use `mise run update-template` to inherit changes from the upstream
meta-template. Python-specific files and questions remain owned by this
repository; merge conflicts in `copier.yml` and `README.md` should preserve
both the inherited tooling configuration and the Python template content.

## Research history

The original brainstorming and the cookiecutter-era drafts live in the
root documents (`CREATE-PYTHON-CLI-MODERN.md`, `PYTHON-CLI-SUMMARY.md`,
`MODERN-TOOLING-COMPARISON.md`, `PYTHON-CLI-MODERN-QUICK-START.md`). The
materialized template supersedes their black/isort/pre-commit/setuptools
stack with uv + prek + ruff; the docs stay as dated history.

## License

Distributed under the `MIT` license — see [LICENSE](LICENSE).
