# Python CLI Template - Modern Quick Start

## TL;DR (45 minutes)

### Step 1: Create Repo (2 min)
```bash
mkdir template-python-cli && cd template-python-cli
git init
```

### Step 2: Copy Files (30 min)
From **CREATE-PYTHON-CLI-MODERN.md**:
- `copier.yml`
- `pyproject.toml.jinja` (no setup.py!)
- `mise.toml.jinja` (task runner)
- `.pre-commit-config.yaml.jinja` (git hooks)
- `scripts/ci.sh.jinja` (complex commands)
- 8 other template files
- `README.md`, `CHANGELOG.md`

### Step 3: Test Locally (5 min)
```bash
pip install copier mise pre-commit

copier copy . /tmp/test-cli --defaults
cd /tmp/test-cli

# Install everything with one command
mise run setup

# Run tests
mise run test

# Check code quality
mise run quality
```

### Step 4: Push to GitHub (5 min)
```bash
git add .
git commit -m "Initial Python CLI template"
git tag v1.0.0
git remote add origin https://github.com/YOURORG/template-python-cli
git push -u origin main --tags
```

### Step 5: Register in Seed System (2 min)
Update `seeds/generic/templates.yml`:
```yaml
- id: python_cli
  name: "Python CLI"
  copier_url: "https://github.com/YOURORG/template-python-cli"
  matchers:
    project_scope: ["CLI tool"]
    programming_language: ["Python"]
```

**Total: ~45 minutes**

---

## What Gets Generated

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
├── pyproject.toml          ✅ Modern packaging (no setup.py!)
├── mise.toml               ✅ Task runner
├── README.md
├── CHANGELOG.md
└── .gitignore
```

All production-ready:
- ✅ Click CLI framework
- ✅ pytest tests
- ✅ GitHub Actions CI/CD
- ✅ Modern packaging (pyproject.toml)
- ✅ Task automation (mise)
- ✅ Pre-commit hooks
- ✅ Code quality (black, isort, ruff, mypy)

---

## Key Improvements

### pyproject.toml (Not setup.py)
- Modern standard (PEP 517/518)
- Unified tool configuration
- Easier to maintain
- Better IDE support

### mise.toml (Not Makefile)
- Cleaner syntax (TOML, not Make)
- Cross-platform (Windows too!)
- Environment variables built-in
- Dependencies between tasks

### .pre-commit-config.yaml
- Automatic code checks before commits
- No need to remember to run tools
- Installed with: `mise run setup`

### scripts/ci.sh
- Complex multi-step commands
- Used by: `mise run ci`
- Organized and reusable

---

## Available Tasks

```bash
mise tasks
```

Generates list:

### Setup
- `mise run setup` - Install deps + setup hooks

### Testing
- `mise run test` - Run tests
- `mise run test-watch` - Watch mode
- `mise run coverage` - With coverage report

### Code Quality
- `mise run lint` - Check code
- `mise run format` - Auto-format
- `mise run format-check` - Check formatting
- `mise run type-check` - Type hints
- `mise run quality` - All checks
- `mise run fix` - Auto-fix issues

### CI/CD
- `mise run ci` - Full pipeline (uses scripts/ci.sh)

### Development
- `mise run cli` - Run the CLI
- `mise run cli-hello` - Run hello command

### Maintenance
- `mise run install-hooks` - Install git hooks
- `mise run run-hooks` - Run all hooks
- `mise run clean` - Clean artifacts
- `mise run clean-all` - Clean + remove venv

---

## File Checklist

From **CREATE-PYTHON-CLI-MODERN.md**:

### Root Configuration
- [ ] `copier.yml`
- [ ] `README.md`
- [ ] `CHANGELOG.md`

### Configuration Files (Step 2)
- [ ] `{{cookiecutter.project_slug}}/pyproject.toml.jinja`
- [ ] `{{cookiecutter.project_slug}}/mise.toml.jinja`
- [ ] `{{cookiecutter.project_slug}}/.pre-commit-config.yaml.jinja`

### Template Files (Step 4)
- [ ] `{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py.jinja`
- [ ] `{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/cli.py.jinja`
- [ ] `{{cookiecutter.project_slug}}/tests/__init__.py`
- [ ] `{{cookiecutter.project_slug}}/tests/test_cli.py.jinja`
- [ ] `{{cookiecutter.project_slug}}/scripts/ci.sh.jinja`
- [ ] `{{cookiecutter.project_slug}}/.github/workflows/test.yml.jinja`
- [ ] `{{cookiecutter.project_slug}}/README.md.jinja`
- [ ] `{{cookiecutter.project_slug}}/CHANGELOG.md.jinja`
- [ ] `{{cookiecutter.project_slug}}/.gitignore`

**Total: 14 files**

---

## Testing Commands

```bash
# Generate from template
copier copy . /tmp/test-cli --defaults

cd /tmp/test-cli

# One command to setup everything!
mise run setup
# This does:
#   - Creates Python venv
#   - Installs project + dev dependencies
#   - Installs pre-commit hooks

# Test the setup
mise run test
# Expected: ✅ 4 tests pass

# Check code quality
mise run quality
# Expected: ✅ All checks pass

# Try the CLI
python -m my_test_cli hello
python -m my_test_cli hello --name Alice
# Expected: Works perfectly!

# Run full CI pipeline
mise run ci
# This runs: linting → type-check → format-check → tests
# Expected: All pass
```

---

## Mise Concepts

### What is mise?

Task runner like Make, but:
- Uses TOML syntax (cleaner)
- Cross-platform (works on Windows)
- Built-in environment variables
- Implicit task dependencies

### Example mise.toml

```toml
[tasks]
# Simple task
test = "pytest tests/"

# Multi-line task
quality = """
ruff check src tests
mypy src
black --check src tests
"""

# Task with environment
[env]
PYTHON = "3.11"
```

---

## Pre-commit Integration

Hooks run automatically on `git commit`:
1. Trailing whitespace removed
2. Large files prevented
3. Ruff linting + fixing
4. Black formatting
5. isort import sorting
6. mypy type checking

If any hook fails:
- Commit is blocked
- Issues are shown
- User can fix and retry

---

## Use in Seed System

Once on GitHub:

```python
from seeds.loader import SeedLoader

loader = SeedLoader()
seed = loader.load_merged_seed()

# Find python_cli template
for template in seed.templates:
    if template.id == 'python_cli':
        print(f'URL: {template.copier_url}')
        # → https://github.com/YOURORG/template-python-cli
```

Users can then generate:
```bash
copier copy https://github.com/YOURORG/template-python-cli my-project
cd my-project
mise run setup
mise run test
```

---

## Next Steps

1. ✅ Read: CREATE-PYTHON-CLI-MODERN.md (understanding)
2. ✅ Create: All files (copy-paste)
3. ✅ Test: `mise run ci`
4. ✅ Push: To GitHub
5. ✅ Register: In seed system

Then:
- Create other templates (python_api, nodejs_web, etc.)
- Build discovery system (suggests templates)
- Wire it all together

---

## Why Modern Tooling?

| Old Way | Modern Way |
|---------|---|
| setup.py | pyproject.toml |
| setup.cfg | pyproject.toml |
| Makefile | mise.toml |
| Manual checks | pre-commit |
| .sh scripts | scripts/ + mise tasks |

Modern is:
- ✅ Cleaner
- ✅ Standardized
- ✅ Better tooling support
- ✅ Easier to maintain
- ✅ Cross-platform

---

## You Now Have

✅ Production-ready Python CLI template
✅ Modern packaging (pyproject.toml)
✅ Task automation (mise.toml)
✅ Automated hooks (pre-commit)
✅ Complex commands (scripts/)
✅ Tests + CI/CD
✅ Ready for seed system

**Start with CREATE-PYTHON-CLI-MODERN.md** 🚀
