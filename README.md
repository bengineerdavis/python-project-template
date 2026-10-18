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

## What it stamps

- `pyproject.toml` — hatchling build, `src/` layout, typer CLI, dev group,
  ruff + mypy + pytest config. Distribution name, import name, and
  console-script name can all differ (`package_name`, `project_slug`,
  `cli_name` — e.g. `redge-cli` / `redge` / `redge`).
- `mise.toml` — python + uv tools; test, lint, format, format-check,
  type-check, quality tasks. Minimal and conventionally shaped so the
  agentic layer's TOML deep-merge (and aboyeur) can extend it.
- `prek.toml` — ruff lint + format hooks only. No generic builtins: in
  layer-stamped projects alint owns whitespace/newline/merge-marker checks
  (no-overlap rule).
- `src/<slug>/` + `tests/` — working typer CLI with a sample command and
  passing tests.
- `.github/workflows/test.yml` — uv-based CI (lint, format, types, tests).
- `LICENSE` — MIT or FSL-1.1-MIT (Fair Source; converts to MIT after two
  years).
- `README.md`, `CHANGELOG.md`, `AGENTS.md` (project map; the layer appends
  its managed section).

## Research history

The original brainstorming and the cookiecutter-era drafts live in the
root documents (`CREATE-PYTHON-CLI-MODERN.md`, `PYTHON-CLI-SUMMARY.md`,
`MODERN-TOOLING-COMPARISON.md`, `PYTHON-CLI-MODERN-QUICK-START.md`). The
materialized template supersedes their black/isort/pre-commit/setuptools
stack with uv + prek + ruff; the docs stay as dated history.
