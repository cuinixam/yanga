# YEP-002: Poks Package Manager

| Field       | Value                              |
|-------------|------------------------------------|
| **Status**  | Draft                              |
| **Created** | 2026-02-08                         |
| **Author**  | -                                  |

## Abstract

This proposal introduces **Poks**, a cross-platform (Windows, Linux, macOS), user-space package manager for Yanga. Inspired by [Scoop](https://scoop.sh/), Poks provides a uniform way to install and manage developer tools (compilers, SDKs, CLI utilities) using simple JSON manifests. It eliminates the need for OS-specific setup scripts and ensures deterministic build environments across different platforms.

## Motivation

### Problem

The existing `ScoopInstall` step only works on Windows. Projects targeting multiple platforms (e.g., cross-compiling for embedded targets from both Windows and Linux hosts) need a way to install host tools (compilers, debuggers, flash tools) regardless of the host OS.

Currently, non-Windows developers must manually install tools or rely on separate scripts, leading to:

- **Inconsistent environments** across developers and CI runners
- **Platform-specific pipeline configurations** with conditional logic
- **No unified caching or version pinning** for host tools on Linux/macOS

### Desired State

A single `PoksInstall` step in the yanga pipeline that:

- Works on Windows, Linux, and macOS
- Follows the same `configs` pattern established by YEP-001
- Installs tools into a user-space directory (no sudo/admin required)
- Provides deterministic, SHA256-verified downloads
- Exposes installed tool paths and environment variables to subsequent pipeline steps

## Poks Overview

Poks is a standalone Python package (`poks`) that manages tool installations through:

- **Buckets**: Git repositories containing application manifests (JSON files describing available versions, download URLs, and checksums)
- **Manifests**: Per-application JSON files listing versions with platform-specific archives
- **Config files** (`poks.json`): Declare which buckets and apps (with pinned versions) to install

### Poks Config Format (`poks.json`)

```json
{
  "buckets": [
    {
      "name": "tools",
      "url": "https://github.com/example/poks-bucket.git"
    }
  ],
  "apps": [
    {
      "name": "arm-gnu-toolchain",
      "version": "13.2.1",
      "bucket": "tools"
    },
    {
      "name": "cmake",
      "version": "3.28.1",
      "bucket": "tools",
      "os": ["windows", "linux"],
      "arch": ["x86_64"]
    }
  ]
}
```

Key properties of a `PoksApp`:

| Field     | Required | Description                                               |
|-----------|----------|-----------------------------------------------------------|
| `name`    | Yes      | Application name (must match manifest filename in bucket) |
| `version` | Yes      | Pinned version string                                     |
| `bucket`  | Yes      | Bucket name or ID to find the manifest in                 |
| `os`      | No       | List of supported OS values (`windows`, `linux`, `macos`). `null` means all. |
| `arch`    | No       | List of supported architectures (`x86_64`, `aarch64`). `null` means all. |

### Poks Manifest Format (per-app, in bucket)

Each bucket contains one JSON manifest per application (e.g., `arm-gnu-toolchain.json`):

```json
{
  "description": "Arm GNU Toolchain",
  "schema_version": "1.0.0",
  "homepage": "https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain",
  "versions": [
    {
      "version": "13.2.1",
      "url": "https://developer.arm.com/-/media/Files/downloads/gnu/${version}/binrel/arm-gnu-toolchain-${version}-${os}-${arch}.${ext}",
      "bin": ["bin"],
      "env": {
        "GNUARMEMB_TOOLCHAIN_PATH": "${dir}"
      },
      "archives": [
        { "os": "windows", "arch": "x86_64", "ext": "zip", "sha256": "abc123..." },
        { "os": "linux", "arch": "x86_64", "ext": "tar.xz", "sha256": "def456..." },
        { "os": "macos", "arch": "aarch64", "ext": "tar.xz", "sha256": "789ghi..." }
      ]
    }
  ]
}
```

### Poks Directory Layout

Poks uses a single root directory (default `~/.poks`) with this structure:

```
~/.poks/
  apps/           # Installed applications
    cmake/
      3.28.1/     # Version-specific install dir
    arm-gnu-toolchain/
      13.2.1/
  buckets/         # Cloned bucket repositories
    <bucket-id>/   # Git clone of bucket
  cache/           # Downloaded archive cache (SHA256-verified)
```

## Proposal

### `PoksInstall` Step

Create a new `PoksInstall` pipeline step in `yanga.steps.poks_install` that mirrors the `ScoopInstall` pattern but delegates to the `poks` library instead of `scoop`.

#### Pipeline Configuration

```yaml
pipeline:
  - install:
    - step: PoksInstall
      module: yanga.steps.poks_install
```

#### Dependency Configuration via `configs`

Following the YEP-001 `ConfigFile` pattern, poks dependencies are declared using `configs` with `id: poks`:

```yaml
# Platform-level: tools needed for this platform
platforms:
  - name: nrf52
    configs:
      - id: poks
        content:
          buckets:
            - name: tools
              url: https://github.com/example/poks-bucket.git
          apps:
            - name: arm-gnu-toolchain
              version: "13.2.1"
              bucket: tools

# Variant-level: additional tools for a specific variant
variants:
  - name: production
    configs:
      - id: poks
        content:
          apps:
            - name: jlink
              version: "7.94"
              bucket: tools

# External file reference
configs:
  - id: poks
    file: poks.json
```

#### Global `poks.json` File

Similar to how `ScoopInstall` supports a root `scoopfile.json`, the `PoksInstall` step supports a `poks.json` file in the project root directory. This is useful for tools needed across all platforms and variants.

#### Dependency Collection and Merging

The step collects poks dependencies from multiple sources in this order:

1. **Global** `poks.json` file in project root (if exists)
2. **Root** configs from `YangaUserConfig.configs` with `id: poks`
3. **Variant** configs from `VariantConfig.configs` with `id: poks`
4. **Platform** configs from `PlatformConfig.configs` with `id: poks`
5. **Variant-Platform** configs from `VariantPlatformsConfig.configs` with `id: poks`

Merge strategy:

- **Buckets**: Deduplicated by name. If the same name appears with different URLs, the first definition wins and a warning is logged.
- **Apps**: Deduplicated by `(name, version, bucket)` tuple. Later definitions are skipped if already present.

#### Step Behavior

```
PoksInstall.run():
  1. Collect dependencies from all config sources
  2. Generate a merged poks.json in the variant build directory
  3. Call poks.install(merged_poks_json) which:
     a. Syncs bucket repositories (clone or pull)
     b. For each app, resolves the manifest and matching archive for the current OS/arch
     c. Downloads archives (with SHA256 verification and caching)
     d. Extracts to ~/.poks/apps/<name>/<version>/
  4. Collect environment updates (PATH additions, custom env vars) from installed apps
  5. Save execution info to JSON file for incremental build support
  6. Update execution context with install dirs and env vars
```

#### Execution Context Updates

After installation, `PoksInstall` updates the `ExecutionContext` so subsequent steps (e.g., CMake build) can find the installed tools:

- **Install directories**: Added via `execution_context.add_install_dirs()` so tool binaries are on PATH
- **Environment variables**: Added via `execution_context.add_env_vars()` for tool-specific variables (e.g., `GNUARMEMB_TOOLCHAIN_PATH`)

#### Incremental Build Support

The step tracks inputs and outputs for yanga's incremental build scheduler:

- **Inputs**: Global `poks.json` (if exists), user config files
- **Outputs**: Generated `poks.json` in build dir, execution info file, install directories

If none of the inputs have changed, the step is skipped but the execution context is still updated from the saved execution info.

### Config Parsing: Step-Owned, Not Domain

Following the YEP-001 principle, yanga's domain layer (`yanga.domain.config`) is **agnostic** to which configuration types exist. It only provides the generic `ConfigFile` abstraction (`id` + `file`/`content`). The domain does not import or depend on any step-specific config models.

The `PoksInstall` step owns its configuration parsing. It uses `collect_configs_by_id(context, "poks")` to retrieve raw `ConfigFile` entries, then parses them into poks-specific models using `parse_config()`. The poks config model lives in the step module (`yanga.steps.poks_install`), not in `yanga.domain.config`.

Since the `poks` library already provides `PoksConfig`, `PoksBucket`, and `PoksApp` dataclasses with JSON serialization, the step can use them directly:

```python
from poks.domain import PoksConfig, PoksBucket, PoksApp
from yanga.domain.config_utils import collect_configs_by_id, parse_config

class PoksInstall(PipelineStep[ExecutionContext]):
    def _collect_dependencies(self) -> PoksConfig:
        collected = PoksConfig()

        # Global poks.json
        if self.global_poks_config_file.exists():
            global_config = PoksConfig.from_json_file(self.global_poks_config_file)
            self._merge_buckets(collected, global_config.buckets)
            self._merge_apps(collected, global_config.apps)

        # Configs from execution context (variant, platform, variant-platform)
        configs = collect_configs_by_id(self.execution_context, "poks")
        for cfg in configs:
            manifest = parse_config(cfg, PoksConfig, self.project_root_dir)
            self._merge_buckets(collected, manifest.buckets)
            self._merge_apps(collected, manifest.apps)

        return collected
```

> **Note:** The existing `ScoopManifest` in `yanga.domain.config` is a legacy placement that predates YEP-001. New steps must not add config models to the domain layer.

## Example: Full Pipeline Configuration

```yaml
pipeline:
  - install:
    - step: PoksInstall
      module: yanga.steps.poks_install
  - gen:
    - step: KConfigGen
      module: yanga.steps.kconfig_gen
  - build:
    - step: GenerateBuildSystemFiles
      module: yanga.steps.execute_build
    - step: ExecuteBuild
      module: yanga.steps.execute_build

platforms:
  - name: nrf52
    toolchain_file: cmake/arm-none-eabi.cmake
    configs:
      - id: poks
        content:
          buckets:
            - name: embedded-tools
              url: https://github.com/example/embedded-tools-bucket.git
          apps:
            - name: arm-gnu-toolchain
              version: "13.2.1"
              bucket: embedded-tools
            - name: cmake
              version: "3.28.1"
              bucket: embedded-tools

variants:
  - name: sensor-node
    components: [hal, drivers, app_sensor]
    configs:
      - id: poks
        content:
          apps:
            - name: nrfjprog
              version: "10.24.0"
              bucket: embedded-tools
```

## Relationship to ScoopInstall

`PoksInstall` is intended as the cross-platform successor to `ScoopInstall`:

| Aspect          | ScoopInstall               | PoksInstall                     |
|-----------------|----------------------------|---------------------------------|
| Platforms       | Windows only               | Windows, Linux, macOS           |
| Tool            | Scoop (PowerShell-based)   | Poks (Python, no system deps)   |
| Manifest format | Scoop JSON                 | Poks JSON (with SHA256, multi-platform archives) |
| Config ID       | `scoop`                    | `poks`                          |
| Root file       | `scoopfile.json`           | `poks.json`                     |
| Install location| Scoop-managed              | `~/.poks/apps/`                 |

Projects can use both steps during a migration period. For new projects, `PoksInstall` is recommended.

## Implementation Plan

1. **Create `PoksInstall` step** in `yanga.steps.poks_install` following the `ScoopInstall` pattern, using `poks` domain models directly (no config models in `yanga.domain.config`)
2. **Add `poks` as a dependency** to yanga's `pyproject.toml`
3. **Add tests** mirroring the `test_scoop_install.py` structure
4. **Update pipeline documentation** in `docs/reference/pipeline.md`

## Benefits

1. **Cross-platform**: Developers on any OS get the same tools at the same versions
2. **Deterministic**: SHA256-verified downloads ensure bit-exact reproducibility
3. **User-space**: No admin/sudo required, installs to `~/.poks/`
4. **Cached**: Archives are cached locally, avoiding redundant downloads
5. **Consistent pattern**: Follows YEP-001 `configs` pattern, familiar to yanga users
6. **Incremental**: Skips already-installed versions, integrates with yanga's build scheduler

## Open Questions

1. Should the poks root directory (`~/.poks`) be configurable via step config or environment variable?
2. Should `PoksInstall` support a `--force` flag to re-download and re-extract all tools?
3. Should bucket sync (git pull) be skippable for offline/air-gapped environments?
