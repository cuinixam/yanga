# yanga-core Extraction Tasks

This document tracks all tasks required to separate `yanga` into:

- **`yanga-core`** — a build-system-agnostic SPL framework (domain model, pipeline orchestration, project discovery)
- **`yanga`** — a cmake-based SPL implementation built on top of `yanga-core`
- **`yanga-steps`** *(tentative name)* — reusable pipeline steps (kconfig, west, scoop, poks) as a separate distribution unit

Tasks are grouped into phases. Phase 1 refactors the current repository in-place, keeping all tests green. Phase 2 extracts repositories.

---

## Phase 1 — In-place Refactoring

### T-001 — Rename `cmake_generators` to `generators` in `PlatformConfig`

**File:** `src/yanga/domain/config.py:80`

**Rationale:**
The field `cmake_generators` carries a CMake-specific name but is typed as `GenericPipelineConfig`, which is already build-system-agnostic. The name leaks cmake semantics into yanga-core's domain model. A user building a Ninja or Make backend against yanga-core would face a confusing config schema.

**Acceptance criteria:**

- `PlatformConfig.cmake_generators` is renamed to `generators`
- All `yanga.yaml` files and documentation updated to use `generators`
- The cmake layer (`builder.py:100`) accesses the field as `platform.generators`
- All existing tests pass
- No occurrences of `cmake_generators` remain in yanga-core domain code

---

### T-002 — Replace `toolchain_file` in `PlatformConfig` with a `ConfigFile` entry

**File:** `src/yanga/domain/config.py:82`

**Rationale:**
`toolchain_file` is a CMake concept (a file passed as `-DCMAKE_TOOLCHAIN_FILE`). Embedding it as a first-class field in `PlatformConfig` makes yanga-core aware of CMake semantics. Using a `ConfigFile` with the well-known ID `"toolchain"` is consistent with how `west`, `scoop`, and `poks` already deliver configuration to their steps, and keeps `PlatformConfig` agnostic.

**Acceptance criteria:**

- `PlatformConfig.toolchain_file: Optional[str]` field is removed
- Toolchain is expressed in `yanga.yaml` as:

  ```yaml
  platforms:
    - name: MyPlatform
      configs:
        - id: toolchain
          file: path/to/toolchain.cmake
  ```

- A helper function (in the cmake layer) retrieves the toolchain path from `platform.configs` by ID `"toolchain"`
- `CMakeBuildSystemGenerator.create_cmake_lists()` and `ExecuteBuild.run()` are updated to use this helper
- All existing toolchain-based tests pass
- No occurrences of `toolchain_file` remain in yanga-core domain or step code

---

### T-003 — Remove `IncludeDirectoriesProvider` from `ExecutionContext`

**Files:**

- `src/yanga/domain/execution_context.py:64–102`
- `src/yanga/steps/kconfig_gen.py` (publisher)
- `src/yanga/cmake/` (consumers)

**Rationale:**
`IncludeDirectoriesProvider` and `include_dirs_providers` on `ExecutionContext` introduce CMake language ("include directories") into the core framework. The mechanism exists so `KConfigGen` can communicate the location of `autoconf.h` to cmake generators. The right abstraction is to publish this information into `data_registry` (the general-purpose inter-step bus that already exists) and let the cmake layer define how to interpret it.

The exact data type and structure published to `data_registry` requires a separate design discussion, as include directories may be global (variant-wide) or component-scoped.

**Acceptance criteria:**

- `IncludeDirectoriesProvider` ABC is removed from `execution_context.py`
- `include_dirs_providers: list[IncludeDirectoriesProvider]` is removed from `ExecutionContext`
- `ExecutionContext.include_directories` property is removed
- `ExecutionContext.add_include_dirs_provider()` method is removed
- A domain type (to be designed) is defined for publishing include directory contributions to `data_registry` — minimum fields: `path: Path`, `scope: Literal["global", "component"]`, optionally `component_name: str`
- `KConfigGen` publishes its output directory via `data_registry` using this type
- All cmake generators that previously consumed `execution_context.include_directories` instead read from `data_registry`
- All existing tests pass

---

### T-004 — Move `domain/targets.py` to the cmake layer

**File:** `src/yanga/domain/targets.py`

**Rationale:**
`TargetType` values — `CUSTOM_COMMAND`, `CUSTOM_TARGET`, `EXECUTABLE`, `OBJECT_LIBRARY` — are CMake constructs. The entire file is consumed exclusively by `CMakeBuildSystemGenerator.create_target_dependencies_file()`. Placing it under `domain/` incorrectly implies it is part of the generic SPL domain model.

**Acceptance criteria:**

- `src/yanga/domain/targets.py` is moved to `src/yanga/cmake/targets.py`
- All import sites updated
- `CMakeBuildSystemGenerator` imports `Target`, `TargetsData`, `TargetType` from `yanga.cmake.targets`
- No imports of `yanga.domain.targets` exist outside of tests for that module
- All existing tests pass

---

### T-005 — Move `steps/execute_build.py` out of the core steps package

**File:** `src/yanga/steps/execute_build.py`

**Rationale:**
`GenerateBuildSystemFiles` and `ExecuteBuild` import directly from `yanga.cmake.*` (builder, cmake_backend, runner). They belong to the cmake layer, not to the generic steps package. Their presence in `steps/` suggests they are framework steps, which they are not — they are the cmake-specific build steps.

**Acceptance criteria:**

- `src/yanga/steps/execute_build.py` is moved to `src/yanga/cmake/steps.py` (or similar location in the cmake package)
- Pipeline configuration files referencing the old classpath (`yanga.steps.execute_build.*`) are updated to the new path
- No files under `src/yanga/domain/` or `src/yanga/steps/` import from `yanga.cmake.*`
- All existing tests pass

---

### T-006 — Extract `create_report_config_file` from `CMakeBuildSystemGenerator` into a standalone step

**File:** `src/yanga/cmake/builder.py:120–158`

**Rationale:**
`create_report_config_file` reads from `data_registry` and assembles a `ReportData` object. This logic is largely generic (grouping registered files by component), but is currently embedded inside the cmake builder. As a result, report configuration is only generated when `GenerateBuildSystemFiles` runs. Moving it to a standalone pipeline step makes the report coordination visible in the pipeline config, independently schedulable, and reusable by non-cmake backends.

**Acceptance criteria:**

- A new pipeline step (e.g., `GenerateReportConfig`) is created, likely in the cmake layer since `build_dir` paths come from `CMakeArtifactsLocator`
- `CMakeBuildSystemGenerator.create_report_config_file()` is removed; `generate()` no longer produces the report config file
- The new step is added to the default pipeline configuration
- Report generation produces identical output to the current implementation
- All existing tests pass

---

### T-007 — Audit and relocate cmake-specific CLI commands

**Files under:** `src/yanga/commands/`

**Rationale:**
The `commands/` package mixes generic orchestration (`run.py`, `base.py`) with cmake-specific tooling commands. The cmake-specific ones must live in the cmake layer or the yanga (cmake) repository so that yanga-core's CLI does not depend on cmake tooling.

| File | Target location |
|---|---|
| `run.py` | yanga-core |
| `base.py` | yanga-core |
| `fix_html_links.py` | yanga-core |
| `report_config.py` | review needed — may be yanga-core |
| `targets.py` | yanga cmake layer |
| `cppcheck_report.py` | yanga cmake layer |
| `gcovr.py` | yanga cmake layer |
| `filter_compile_commands.py` | yanga cmake layer |

**Acceptance criteria:**

- Each file listed above is verified against its import graph
- cmake-specific command files are moved to a `cmake/commands/` or `cmake/` subpackage
- `ymain.py` registers commands from both the core and cmake locations without circular imports
- All CLI commands remain functional
- All existing tests pass

---

### T-008 — Verify `yide.py` cmake coupling

**File:** `src/yanga/yide.py`

**Rationale:**
`yide.py` generates IDE project files. If it reads `compile_commands.json` or any other cmake-generated artifact it must move to the yanga cmake layer, not yanga-core. This needs explicit verification before the split.

**Acceptance criteria:**

- Import graph of `yide.py` is documented
- If cmake-specific: move to `cmake/` and register in cmake CLI
- If generic: remains in yanga-core with no cmake imports
- All existing tests pass

---

## Phase 2 — Repository Extraction

### T-009 — Create the `yanga-core` repository

**Rationale:**
After Phase 1 refactoring the cmake-specific code is isolated. yanga-core can be extracted as a standalone installable package that provides the SPL framework without any cmake dependency.

**Acceptance criteria:**

- `yanga-core` repository created with its own `pyproject.toml`
- Contains: `domain/` (config, components, artifacts, execution_context, project_slurper, reports), `commands/run.py`, `commands/base.py`, `commands/fix_html_links.py`
- No imports of `yanga.cmake.*` exist anywhere in the package
- Published to PyPI (or internal registry) as `yanga-core`
- Package includes a minimal CLI entry point for `run` command
- Test suite covers all extracted modules

---

### T-010 — Create the `yanga-steps` repository *(or equivalent distribution strategy)*

**Rationale:**
Steps (`kconfig_gen`, `west_install`, `scoop_install`, `poks_install`) are reusable pipeline steps that are independent of both the cmake build system and the core framework's release cycle. A breaking change in a step should not force a version bump on yanga-core. They should be distributed separately.

**Acceptance criteria:**

- A separate package (or packages) is defined for the reusable steps
- Each step package declares `yanga-core` as a dependency (for `PipelineStep[ExecutionContext]`)
- Steps can be imported via their new classpath in pipeline configs
- Version of steps is decoupled from version of yanga-core
- All existing step tests pass against the new package structure

---

### T-011 — Refactor `yanga` to depend on `yanga-core`

**Rationale:**
After extraction, the yanga repository retains only cmake-specific code. It becomes a thin cmake implementation layer on top of yanga-core, analogous to how a user would build their own build-system adapter.

**Acceptance criteria:**

- `yanga` repository `pyproject.toml` declares `yanga-core` as a dependency
- `yanga` package contains: `cmake/`, cmake-specific `steps/`, cmake-specific `commands/`
- `ymain.py` composes the full CLI from yanga-core commands and cmake-specific commands
- `yanga.yaml` pipeline configs reference step classpaths from both `yanga-core` (or steps package) and `yanga`
- End-to-end build of an example project produces identical output
- Full test suite passes

---

## Open Design Questions

| ID | Question | Blocking |
|---|---|---|
| DQ-001 | What is the data type(s) published to `data_registry` for include directory contributions? Global vs component-scoped? Multiple providers per component? | T-003 |
| DQ-002 | Should `yanga-steps` be a single package or individual packages per step (e.g., `yanga-step-kconfig`, `yanga-step-west`)? | T-010 |
| DQ-003 | `report_config.py` command — does it depend on cmake artifacts or is it generic? | T-007 |
| DQ-004 | Should yanga-core ship a default empty CLI or no CLI at all (pure library)? | T-009 |
