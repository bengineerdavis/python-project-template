# Python CLI Template - Modern vs Old Comparison

## What Changed

### ❌ Removed
- `setup.py` - Replaced by pyproject.toml
- `Makefile` - Replaced by mise.toml
- `requirements.txt` / `requirements-dev.txt` - Moved to pyproject.toml
- No automatic hooks

### ✅ Added
- `pyproject.toml` - Single source of truth
- `mise.toml` - Task automation
- `.pre-commit-config.yaml` - Automatic code checks
- `scripts/ci.sh` - Multi-step commands
- Automatic hook installation

---

## Side-by-Side Comparison

### Packaging: setup.py → pyproject.toml

**Old (setup.py):**
```python
from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='my-cli',
    version='0.1.0',
    author='Name',
    author_email='email@example.com',
    # ... 20 more lines ...
)
```

**New (pyproject.toml):**
```toml
[build-system]
requires = ["setuptools>=65", "setuptools-scm>=7"]

[project]
name = "my-cli"
version = "0.1.0"
authors = [{name = "Name", email = "email@example.com"}]
# ... cleaner, more declarative
```

**Benefits:**
- ✅ Standard (PEP 517/518)
- ✅ No Python code to execute
- ✅ Better IDE support
- ✅ Tool configuration in one place

---

### Task Running: Makefile → mise.toml

**Old (Makefile):**
```makefile
.PHONY: test lint format

test:
	pytest tests/

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	isort src tests

quality: lint format
	echo "All checks passed"
```

**New (mise.toml):**
```toml
[tasks]
test = "pytest tests/"

lint = """
ruff check src tests
mypy src
"""

format = """
black src tests
isort src tests
"""

quality = """
mise run lint
mise run format
echo "All checks passed"
"""
```

**Benefits:**
- ✅ Cleaner TOML syntax
- ✅ Cross-platform (Windows works!)
- ✅ No tab issues
- ✅ Built-in environment variables
- ✅ Better task dependencies

---

### Dependencies Management

**Old (setup.py + requirements.txt):**
```
setup.py: install_requires = ["click>=8.0.0"]
requirements.txt: click>=8.0.0
requirements-dev.txt: pytest, black, isort, ...
.github/workflows/test.yml: pip install -r requirements-dev.txt
```

**New (pyproject.toml only):**
```toml
[project]
dependencies = ["click>=8.0.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=23.0.0", "isort>=5.0.0"]
```

**Benefits:**
- ✅ Single source of truth
- ✅ Optional dependencies are explicit
- ✅ No sync issues between files
- ✅ Install with: `pip install -e ".[dev]"`

---

### Code Quality Automation

**Old (Manual Checks):**
```bash
# Developer must remember to run:
black src tests
isort src tests
ruff check src tests
mypy src
pytest

# If forgotten, CI catches it later
```

**New (Pre-commit Hooks):**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    hooks:
      - id: black
```

Installed with: `mise run setup`

Runs automatically on: `git commit`

**Benefits:**
- ✅ Catches issues before commit
- ✅ Can auto-fix
- ✅ Developer doesn't have to remember
- ✅ CI is faster (fewer failures)

---

### Complex Commands

**Old (separate .sh files):**
```bash
# scripts/check.sh
pytest
black --check src tests
isort --check-only src tests

# scripts/lint.sh
ruff check src tests
mypy src

# Makefile
.PHONY: ci
ci:
	bash scripts/check.sh && bash scripts/lint.sh
```

**New (organized scripts + mise):**
```toml
# mise.toml - unified task runner
[tasks]
ci = "sh scripts/ci.sh"

# scripts/ci.sh - organized multi-step
#!/bin/bash
set -e
ruff check src tests
mypy src
black --check src tests
isort --check-only src tests
pytest
```

**Benefits:**
- ✅ Scripts stay organized
- ✅ Called from mise tasks
- ✅ Clear error handling (set -e)
- ✅ Reusable and composable

---

## Setup Process

### Old Way
```bash
# User has to manually run everything
python -m venv venv
source venv/bin/activate
pip install setuptools
pip install -e .
pip install -r requirements-dev.txt
pip install -r requirements.txt
# Then remember to install pre-commit?
```

### New Way
```bash
# One command does it all
mise run setup
# This does:
#   1. Creates venv
#   2. Installs dependencies
#   3. Installs pre-commit hooks
```

**Much better!**

---

## Development Workflow

### Old Way
```bash
# Developer has to remember commands
black src tests           # Format
isort src tests           # Sort imports
ruff check src tests      # Lint
mypy src                  # Type check
pytest                    # Test

# If they forget, it fails in CI later
```

### New Way
```bash
# Pre-commit catches issues on commit
git commit                # Hooks run automatically

# Or run manually
mise run quality          # All checks at once

# Or run specific checks
mise run test
mise run lint
mise run format
```

---

## CI/CD

### Old (GitHub Actions)
```yaml
- name: Install dependencies
  run: |
    pip install setuptools
    pip install -e ".[dev]"

- name: Run linting
  run: ruff check src tests

- name: Run type check
  run: mypy src

- name: Run tests
  run: pytest
```

### New (GitHub Actions + mise)
```yaml
- name: Run CI
  run: |
    pip install mise
    mise run ci
    # Calls: scripts/ci.sh which has all checks
```

**Cleaner and reusable!**

---

## Summary of Advantages

| Aspect | Old | New |
|--------|-----|-----|
| **Packaging** | setup.py | pyproject.toml ✅ |
| **Tool Config** | Scattered | pyproject.toml ✅ |
| **Task Running** | Makefile | mise.toml ✅ |
| **Dependencies** | Multiple files | One file ✅ |
| **Code Quality** | Manual | Pre-commit ✅ |
| **Setup** | Many steps | One command ✅ |
| **Cross-platform** | Problems on Windows | Works everywhere ✅ |
| **IDE Support** | Basic | Excellent ✅ |

---

## Migration Path

If you have an old template:

1. **Rename `setup.py` → Move to `pyproject.toml`**
   ```bash
   # Extract metadata from setup.py
   # Put it in pyproject.toml [project] section
   # Put build config in [build-system] section
   # Delete setup.py
   ```

2. **Replace `Makefile` with `mise.toml`**
   ```bash
   # For each make target:
   #   Create a [tasks] section in mise.toml
   # Delete Makefile
   ```

3. **Add `.pre-commit-config.yaml`**
   ```bash
   # Copy from this template
   # Run: pre-commit install
   ```

4. **Organize scripts**
   ```bash
   # Move complex commands to scripts/
   # Call them from mise tasks
   ```

---

## Why This Matters

### For Your Users
```bash
# Old way - confusing
pip install -e .
pip install -r requirements-dev.txt
python -m pytest
python -m black src tests

# New way - clear and simple
mise run setup
mise run test
mise run format
```

### For Your CI/CD
```yaml
# Old - many steps
- run: pip install -e ".[dev]"
- run: ruff check
- run: black --check
- run: pytest

# New - one command
- run: mise run ci
```

### For Maintenance
```
# Old - scattered config
setup.py, setup.cfg, pyproject.toml, Makefile, .pre-commit-config.yaml

# New - organized
pyproject.toml (Python config)
mise.toml (Tasks)
.pre-commit-config.yaml (Hooks)
scripts/ (Complex commands)
```

---

## What Developers Will Love

✅ **One-command setup:** `mise run setup`
✅ **Clear task lists:** `mise tasks`
✅ **Automatic hooks:** Catches issues on commit
✅ **Modern standards:** PEP 517/518 compliant
✅ **Cross-platform:** Works on Windows, Mac, Linux
✅ **Better docs:** pyproject.toml is self-documenting
✅ **IDE friendly:** Better autocomplete and validation
✅ **CI friendly:** Easier to integrate with GitHub Actions

---

## You're Now Using

- ✅ **PEP 517/518** - Modern Python packaging standard
- ✅ **mise** - Modern task runner (like Task, dagger, or taskfile)
- ✅ **pre-commit** - Automated code quality
- ✅ **Script organization** - Clean and reusable

This is the **current best practice** for Python projects! 🚀
