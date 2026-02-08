# Yanga Development Guide for AI Agents

## Project Overview

Yanga is a C/C++ build system generator, it uses yaml file as configuration and generates the CMake build files.
It supports Software Product Line (SPL) development with feature model, variants, components, and platform-specific configurations.

## Core Architecture

- **Domain Layer**: `src/yanga/domain/` - Core business logic and data models
- **Backend Layer**: `src/yanga/cmake/` - CMake-specific build system generators
- **Commands Layer**: `src/yanga/commands/` - CLI command implementations
- **Kickstart**: `src/yanga/kickstart/` - Project template system

### Key Domain Concepts

- **ExecutionContext**: Central coordination object containing project state, components, and user requests
- **Component**: Represents a buildable unit with sources, tests, and metadata (`src/yanga/domain/components.py`)
- **VariantConfig**: SPL variant definitions with feature configurations
- **PlatformConfig**: Platform-specific build settings and toolchain configurations

## Development Workflow

### Environment Setup

```bash
pipx install pypeline-runner
pypeline run  # Bootstraps project and runs full pipeline
```

### Key Commands

- `pypeline run --step PyTest --single` - Run tests only
- `pypeline run --step PreCommit --single` - Run linters/formatters
- `pypeline run --step Docs --single` - Generate documentation
- `yanga init <dir>` - Create new Yanga project from templates
- `yanga run` - Execute build pipeline for variants/components

### VS Code Integration

Use predefined tasks via Command Palette:

- "Tasks: Run Task" → "run tests"
- "Tasks: Run Task" → "run pre-commit checks"
- "Tasks: Run Task" → "generate docs"

## Code Patterns & Conventions

### Configuration Management

Uses **mashumaro** dataclasses with YAML serialization:

```python
@dataclass
class MyConfig(DataClassDictMixin):
    field: str
    # Load with: MyConfig.from_dict(yaml.safe_load(content))
```

### Error Handling

Use `UserNotificationException` from `py-app-dev` for user-facing errors:

```python
from py_app_dev.core.exceptions import UserNotificationException
raise UserNotificationException("Clear message for users")
```

### Logging & Timing

Prefer `py-app-dev` logging utilities:

```python
from py_app_dev.core.logging import logger, time_it

@time_it("operation_name")
def my_function():
    logger.info("Message")
```

### Testing Patterns

- Use `conftest.py` fixtures for common test setup
- Mock `ProjectArtifactsLocator.locate_artifact` for file location tests
- Create `ExecutionContext` mocks for domain testing
- Test files follow pattern: `test_<module>.py`

## Project Structure Conventions

### Template System

Project templates in `src/yanga/kickstart/templates/`:

- `mini/` - Minimal project template
- `max/` - Full-featured project template
- `common/` - Shared template components

### Dynamic Module Loading

Build steps and CMake generators are loaded dynamically from:

- `src/yanga/steps/` - Custom pipeline steps
- `src/yanga/cmake/` - CMake generators
- User configuration can reference these modules by name

### Configuration Files

- `pypeline.yaml` - Development pipeline configuration
- `pyproject.toml` - Package metadata and tool configuration
- `build_exe.spec` - PyInstaller executable build specification

## Integration Points

### pypeline Integration

Yanga uses pypeline for development automation. Steps are defined in `pypeline.yaml` and can be executed individually or as a pipeline.

### CMake Backend

The `yanga.cmake` module contains generators that produce CMake files for different build targets (executables, tests, coverage, etc.).

### West Integration

Supports Zephyr West tool for dependency management via `WestManifest` configuration.

## Development Guidelines

### Adding New Features

1. Create domain models in `src/yanga/domain/`
2. Implement CLI commands in `src/yanga/commands/`
3. Add backend generators in `src/yanga/cmake/` if needed
4. Write tests following existing patterns
5. Update documentation in `docs/`

### Code Quality

- Ruff handles linting/formatting (configured in `pyproject.toml`)
- Pre-commit hooks enforce code standards
- Type hints are required (`py.typed` marker present)
- Docstrings follow standard conventions but are not required for all functions

### Dependencies

- Core: `typer` (CLI), `mashumaro` (serialization), `loguru` (logging)
- Build: `pypeline-runner` (automation), `pyinstaller` (executable builds)
- Dev: `pytest` (testing), `ruff` (linting), `pre-commit` (hooks)

## Coding Guidelines

- Always include full **type hints** (functions, methods, public attrs, constants).
- Prefer **pythonic** constructs: context managers, `pathlib`, comprehensions when clear, `enumerate`, `zip`, early returns, no over-nesting.
- Follow **SOLID**: single responsibility; prefer composition; program to interfaces (`Protocol`/ABC); inject dependencies.
- **Naming**: descriptive `snake_case` vars/funcs, `PascalCase` classes, `UPPER_SNAKE_CASE` constants. Avoid single-letter identifiers (including `i`, `j`, `a`, `b`) except in tight math helpers.
- Code should be **self-documenting**. Use docstrings only for public APIs or non-obvious rationale/constraints; avoid noisy inline comments.
- Errors: raise specific exceptions; never `except:` bare; add actionable context.
- Imports: no wildcard; group stdlib/third-party/local, keep modules small and cohesive.
- Testability: pure functions where possible; pass dependencies, avoid globals/singletons.
- tests: use `pytest`; keep the tests to a minimum; use parametrized tests when possible; do no add useless comments; the tests shall be self-explanatory.
- pytest fixtures: use them to avoid code duplication; use `conftest.py` for shared fixtures. Use `tmp_path` in case of file system operations.

## Definition of Done

Changes are NOT complete until:

- `pypeline run` executes with **zero failures**
- **All new functionality has tests** - never skip writing tests for new code
- Test coverage includes edge cases and error conditions
