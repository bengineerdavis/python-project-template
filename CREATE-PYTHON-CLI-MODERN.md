# Python CLI Template - Modern Tooling (pyproject.toml + mise + precommit)

## Overview

Updated template using:
- **pyproject.toml** - Modern Python packaging (no setup.py)
- **mise.toml** - Task runner (instead of Makefile)
- **.pre-commit-config.yaml** - Git hooks
- **scripts/** - Complex multi-step commands

---

## Step 1: Create Repository

```bash
mkdir template-python-cli
cd template-python-cli
git init
git config user.email "you@example.com"
git config user.name "Your Name"
```

---

## Step 2: Create Root Configuration Files

### `copier.yml`

```yaml
_templates_suffix: .jinja
_envops:
  block_end_string: "%}"
  block_start_string: "{%"
  variable_end_string: "}}"
  variable_start_string: "{{"

_jinja_extensions:
  - jinja2.ext.loopcontrols

project_name:
  type: str
  help: "Project name (e.g., 'My CLI Tool')"

project_slug:
  type: str
  default: "{{ project_name.lower().replace(' ', '_').replace('-', '_') }}"
  help: "Python import name (lowercase, underscores)"

description:
  type: str
  help: "Project description"

author_name:
  type: str
  help: "Author name"

author_email:
  type: str
  help: "Author email"

python_version:
  type: str
  default: "3.11"
  help: "Minimum Python version"

use_github_actions:
  type: bool
  default: true
  help: "Add GitHub Actions CI/CD?"

license:
  type: str
  default: "MIT"
  choices:
    - MIT
    - Apache 2.0
    - GPL 3.0
    - BSD 3-Clause
  help: "License"
```

### `README.md`

```markdown
# Python CLI Copier Template

A production-ready Copier template for Python CLI applications using modern tooling.

## Features

- ✅ Click-based CLI framework
- ✅ Modern project structure (src layout)
- ✅ pytest testing
- ✅ pyproject.toml packaging (PEP 517/518)
- ✅ mise.toml task runner
- ✅ Pre-commit hooks
- ✅ GitHub Actions CI/CD
- ✅ Type hints (mypy)
- ✅ Code quality tools (black, isort, ruff)

## Usage

```bash
copier copy https://github.com/YOURORG/template-python-cli /path/to/new-project
cd new-project
mise run setup
mise run test
```

## Generated Project Structure

```
my-cli-tool/
├── src/
│   └── my_cli_tool/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   └── test_cli.py
├── scripts/
│   └── ci.sh
├── .github/
│   └── workflows/
│       └── test.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── mise.toml
├── README.md
├── CHANGELOG.md
└── .gitignore
```
```

### `CHANGELOG.md`

```markdown
# Template Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Modern Python packaging (pyproject.toml)
- mise task runner
- Pre-commit hooks
- Click CLI framework
- Pytest test setup
- GitHub Actions CI/CD
```

---

## Step 3: Create Directory Structure

```bash
mkdir -p "{{cookiecutter.project_slug}}"/{src,tests,scripts,.github/workflows}
touch "{{cookiecutter.project_slug}}"/scripts/.gitkeep
```

---

## Step 4: Create Template Files

### 4a. `{{cookiecutter.project_slug}}/pyproject.toml.jinja`

```toml
[build-system]
requires = ["setuptools>=65", "setuptools-scm>=7"]
build-backend = "setuptools.build_meta"

[project]
name = "{{cookiecutter.project_slug}}"
version = "0.1.0"
description = "{{cookiecutter.description}}"
readme = "README.md"
requires-python = ">={{cookiecutter.python_version}}"
license = {text = "{{cookiecutter.license}}"}
authors = [
    {name = "{{cookiecutter.author_name}}", email = "{{cookiecutter.author_email}}"},
]
keywords = ["cli", "command-line"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
{{cookiecutter.project_slug}} = "{{cookiecutter.project_slug}}.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers -v"
markers = [
    "integration: marks tests as integration (deselect with '-m \"not integration\"')",
]

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]
ignore = ["E501"]  # line too long

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

### 4b. `{{cookiecutter.project_slug}}/mise.toml.jinja`

```toml
[env]
PYTHON = "{{cookiecutter.python_version}}"

[tasks]

# Setup tasks
setup = """
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install
"""

# Testing tasks
test = """
pytest tests/
"""

test-watch = """
pytest-watch tests/ -- --clear
"""

coverage = """
pytest --cov={{cookiecutter.project_slug}} --cov-report=html --cov-report=term
"""

# Code quality tasks
lint = """
ruff check src tests
"""

format = """
black src tests
isort src tests
"""

format-check = """
black --check src tests
isort --check-only src tests
"""

type-check = """
mypy src
"""

quality = """
mise run lint
mise run type-check
mise run format-check
"""

fix = """
ruff check --fix src tests
black src tests
isort src tests
"""

# CI/CD tasks
ci = """
sh scripts/ci.sh
"""

# Development
cli = """
python -m {{cookiecutter.project_slug}}.cli
"""

cli-hello = """
python -m {{cookiecutter.project_slug}}.cli hello --name "{{cookiecutter.project_name}}"
"""

install-hooks = """
pre-commit install
pre-commit install --hook-type commit-msg
"""

run-hooks = """
pre-commit run --all-files
"""

# Documentation
docs = """
echo "Documentation can be added here"
"""

# Clean tasks
clean = """
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
rm -rf build dist *.egg-info
rm -rf .pytest_cache .mypy_cache htmlcov
"""

clean-all = """
mise run clean
rm -rf venv
"""
```

### 4c. `{{cookiecutter.project_slug}}/.pre-commit-config.yaml.jinja`

```yaml
# Pre-commit hooks configuration
# Install: pre-commit install
# Run manually: pre-commit run --all-files

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements
      - id: mixed-line-ending

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
        additional_dependencies: []
```

### 4d. `{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py.jinja`

```python
"""{{cookiecutter.project_name}}."""

__version__ = '0.1.0'
__author__ = '{{cookiecutter.author_name}}'
__email__ = '{{cookiecutter.author_email}}'

__all__ = ['__version__', '__author__', '__email__']
```

### 4e. `{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/cli.py.jinja`

```python
"""CLI for {{cookiecutter.project_name}}."""

import click


@click.group()
@click.version_option(version='0.1.0')
def main() -> None:
    """{{cookiecutter.description}}"""
    pass


@main.command()
@click.option('--name', default='World', help='Name to greet')
def hello(name: str) -> None:
    """Simple hello command."""
    click.echo(f'Hello {name}!')


if __name__ == '__main__':
    main()
```

### 4f. `{{cookiecutter.project_slug}}/tests/__init__.py`

```python
"""Tests package."""
```

### 4g. `{{cookiecutter.project_slug}}/tests/test_cli.py.jinja`

```python
"""Tests for CLI module."""

from click.testing import CliRunner
from {{cookiecutter.project_slug}}.cli import main, hello


def test_main_help() -> None:
    """Test main help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "{{cookiecutter.description}}" in result.output


def test_main_version() -> None:
    """Test version flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_hello_default() -> None:
    """Test hello command with default."""
    runner = CliRunner()
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert "Hello World!" in result.output


def test_hello_with_name() -> None:
    """Test hello command with name."""
    runner = CliRunner()
    result = runner.invoke(main, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello Alice!" in result.output
```

### 4h. `{{cookiecutter.project_slug}}/scripts/ci.sh.jinja`

```bash
#!/bin/bash
# CI/CD script - runs all quality checks and tests
# Used by: mise run ci

set -e  # Exit on first error

echo "🔍 Running CI pipeline..."
echo ""

# Code quality checks
echo "📋 Running linting..."
ruff check src tests
echo "✅ Linting passed"
echo ""

# Type checking
echo "🔎 Running type checks..."
mypy src
echo "✅ Type checks passed"
echo ""

# Format checking
echo "📐 Checking code format..."
black --check src tests
isort --check-only src tests
echo "✅ Format check passed"
echo ""

# Tests with coverage
echo "🧪 Running tests with coverage..."
pytest --cov={{cookiecutter.project_slug}} --cov-report=term-missing
echo "✅ Tests passed"
echo ""

echo "🎉 All checks passed!"
```

### 4i. `{{cookiecutter.project_slug}}/.gitignore`

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
.mypy_cache/
.dmypy.json
dmypy.json
```

### 4j. `{{cookiecutter.project_slug}}/.github/workflows/test.yml.jinja`

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: {% raw %}${{ matrix.python-version }}{% endraw %}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check src tests

      - name: Type check with mypy
        run: mypy src

      - name: Format check
        run: |
          black --check src tests
          isort --check-only src tests

      - name: Test with pytest
        run: pytest --cov={{cookiecutter.project_slug}} --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 4k. `{{cookiecutter.project_slug}}/README.md.jinja`

```markdown
# {{cookiecutter.project_name}}

{{cookiecutter.description}}

## Installation

Install from source:

```bash
git clone https://github.com/YOURORG/{{cookiecutter.project_slug}}.git
cd {{cookiecutter.project_slug}}
mise run setup
```

## Usage

```bash
# Show help
{{cookiecutter.project_slug}} --help

# Run hello command
{{cookiecutter.project_slug}} hello
{{cookiecutter.project_slug}} hello --name "Alice"
```

## Development

### Setup

```bash
mise run setup
```

### Running Tests

```bash
# Run tests
mise run test

# Run tests with coverage
mise run coverage

# Watch mode
mise run test-watch
```

### Code Quality

```bash
# Format code
mise run format

# Check formatting
mise run format-check

# Lint code
mise run lint

# Type check
mise run type-check

# Run all quality checks
mise run quality

# Fix issues
mise run fix
```

### Git Hooks

Hooks are installed automatically during setup. Run manually with:

```bash
mise run run-hooks
```

## Available Tasks

```bash
mise tasks
```

Common tasks:
- `mise run setup` - Initial setup
- `mise run test` - Run tests
- `mise run quality` - Run all quality checks
- `mise run fix` - Auto-fix issues
- `mise run ci` - Full CI pipeline
- `mise run clean` - Clean artifacts
- `mise run clean-all` - Clean including venv

## License

{{cookiecutter.license}}

## Author

{{cookiecutter.author_name}} <{{cookiecutter.author_email}}>
```

### 4l. `{{cookiecutter.project_slug}}/CHANGELOG.md.jinja`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - {{cookiecutter.now.strftime('%Y-%m-%d')}}

### Added
- Initial release
- Basic CLI structure with Click
- Test suite with pytest
- Modern Python packaging (pyproject.toml)
- mise task runner
- Pre-commit hooks
- GitHub Actions CI/CD
```

---

## Step 5: Create Directory Structure

```bash
mkdir -p "{{cookiecutter.project_slug}}"/{src/{{cookiecutter.project_slug}},tests,scripts,.github/workflows}
```

---

## Step 6: Commit to Git

```bash
git add .
git commit -m "Initial Python CLI Copier template"
git tag v1.0.0
```

---

## Step 7: Test Locally

```bash
# Generate a test project
copier copy . /tmp/test-cli --defaults

cd /tmp/test-cli

# Setup environment
mise run setup

# Run tests
mise run test

# Check quality
mise run quality

# Try the CLI
python -m {{cookiecutter.project_slug}}.cli hello
python -m {{cookiecutter.project_slug}}.cli hello --name "Test"
```

---

## Step 8: Push to GitHub

```bash
git remote add origin https://github.com/YOURORG/template-python-cli
git push -u origin main --tags
```

---

## What Gets Generated

When user runs the template, they get:

```
my-cli-tool/
├── src/my_cli_tool/
│   ├── __init__.py
│   └── cli.py
├── tests/
│   ├── __init__.py
│   └── test_cli.py
├── scripts/
│   └── ci.sh
├── .github/workflows/
│   └── test.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── mise.toml
├── README.md
├── CHANGELOG.md
└── .gitignore
```

Ready to use:
```bash
cd my-cli-tool
mise run setup        # Install deps + setup hooks
mise run test         # Run tests
mise run quality      # Check code quality
my-cli-tool hello     # Run CLI
```

---

## Key Improvements Over setup.py

| Feature | setup.py | pyproject.toml |
|---------|----------|---|
| **Standard** | Old | Modern (PEP 517/518) |
| **Readability** | Imperative | Declarative |
| **Build System** | Tightly coupled | Decoupled |
| **Dependencies** | setup.py only | Both |
| **Tool Config** | Scattered | Unified |

---

## mise vs Makefile

| Feature | Makefile | mise.toml |
|---------|----------|---|
| **Language** | Make syntax | TOML |
| **Dependencies** | Manual order | Explicit |
| **Cross-platform** | Unix-like only | Works everywhere |
| **Env vars** | Shell syntax | Native support |
| **Readability** | Hard tabs | Clear |

---

## Pre-commit Integration with mise

Pre-commit hooks are:
1. **Installed** by `mise run setup`
2. **Run manually** with `mise run run-hooks`
3. **Configured** in `.pre-commit-config.yaml`
4. **CI-checked** in GitHub Actions

Hooks run:
- Black (formatting)
- isort (import sorting)
- Ruff (linting + fixing)
- mypy (type checking)
- Standard checks (trailing whitespace, etc)

---

## Scripts Directory

The `scripts/ci.sh` file demonstrates how complex commands can be organized:

```bash
# Runs multiple checks in sequence
# Uses: mise run ci
# Or: bash scripts/ci.sh

ruff check src tests
mypy src
black --check src tests
isort --check-only src tests
pytest --cov={{cookiecutter.project_slug}} --cov-report=term-missing
```

All results are captured and checked for errors (set -e).

---

## Complete Setup Flow

```bash
# User gets the template
copier copy TEMPLATE_URL my-project
cd my-project

# One command to setup everything
mise run setup
# This does:
# 1. Creates venv
# 2. Installs dependencies
# 3. Installs pre-commit hooks

# Develop normally
# Commits are checked automatically by pre-commit

# Run any task
mise run test
mise run quality
mise run format
mise run fix

# CI runs the full pipeline
mise run ci
```

---

## Summary

This template provides:
- ✅ Modern Python packaging (pyproject.toml)
- ✅ Task automation (mise.toml)
- ✅ Automated code checks (pre-commit)
- ✅ Complex commands organized (scripts/)
- ✅ Zero setup friction
- ✅ CI/CD ready
