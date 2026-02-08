# YEP-001: Generic Configuration Files

| Field       | Value                              |
|-------------|------------------------------------|
| **Status**  | Accepted                           |
| **Created** | 2026-02-08                         |
| **Author**  | -                                  |

## Abstract

This proposal introduces a generic `ConfigFile` abstraction to replace hard-coded manifest fields (`west_manifest`, `scoop_manifest`) in yanga's configuration. The goal is to make yanga extensible without modification when new dependency management tools or configuration needs arise.

## Motivation

### Problem

Currently, yanga's `PlatformConfig`, `VariantConfig`, and `VariantPlatformsConfig` classes contain hard-coded fields for specific manifest types:

```python
@dataclass
class PlatformConfig:
    west_manifest: Optional[WestManifest] = None
    scoop_manifest: Optional[ScoopManifest] = None
```

This design violates the **Open/Closed Principle**: adding support for a new dependency manager (e.g., Conan, vcpkg, pip) requires modifying yanga's core domain classes.

### Current State

- `west_manifest` and `scoop_manifest` are defined in:
  - `PlatformConfig`
  - `VariantConfig`
  - `VariantPlatformsConfig`
- Each step (`WestInstall`, `ScoopInstall`) directly accesses these typed fields
- Global manifest files (`west.yaml`, `scoopfile.json`) are also supported in the project root

### Desired State

- Yanga is agnostic to configuration types, it stores references, not domain-specific structures
- Steps own their configuration parsing logic
- New dependency managers can be added by creating new steps without modifying yanga

## Proposal

### ConfigFile Dataclass

Introduce a generic `ConfigFile` type:

```python
@dataclass
class ConfigFile(BaseConfigDictMixin):
    """Generic configuration file reference."""
    #: Unique identifier used by steps to locate their configuration
    id: str
    #: Path to an external configuration file (relative to yanga.yaml)
    file: Optional[Path] = None
    #: Inline configuration content
    content: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.file is None and self.content is None:
            raise ValueError(f"ConfigFile '{self.id}' must have either 'file' or 'content'")
```

### Configuration Schema

Add `configs` field at three levels:

```yaml
# Root level (yanga.yaml)
configs:
  - id: west
    file: west.yaml
  - id: scoop
    file: scoopfile.json

platforms:
  - name: nrf52
    configs:
      - id: west
        content:
          remotes:
            - name: zephyr
              url: https://github.com/zephyrproject-rtos/zephyr
          projects:
            - name: zephyr
              remote: zephyr
              revision: v3.5.0

variants:
  - name: production
    configs:
      - id: scoop
        content:
          apps:
            - Name: arm-gnu-toolchain
```

### Step Responsibility

Steps delegate config collection to a shared utils module:

```python
from yanga.domain.config_utils import collect_configs_by_id, parse_config

class WestInstall(PipelineStep):
    def _collect_manifests(self) -> list[WestManifest]:
        configs = collect_configs_by_id(self.execution_context, "west")
        return [parse_config(cfg, WestManifest) for cfg in configs]
```

### Collection Order

Configs are collected in this order (earlier entries have lower priority, later entries can override):

1. **Root** - from `YangaUserConfig.configs`
2. **Variant** - from `VariantConfig.configs`
3. **Platform** - from `PlatformConfig.configs`
4. **Variant-Platform** - from `VariantPlatformsConfig.configs`

### Merge Semantics

Steps define their own merge strategy:

- **Additive**: Combine all configs (e.g., West projects accumulate)
- **Override**: Later configs replace earlier ones
- **Custom**: Step-specific merge logic

## Migration Path

### Phase 1: Add New Field (Non-breaking)

1. Add `configs: list[ConfigFile]` to `YangaUserConfig`, `PlatformConfig`, `VariantConfig`
2. Steps check both legacy fields and new `configs` field
3. Document new approach

### Phase 2: Deprecation Warning

1. Emit deprecation warnings when legacy fields are used
2. Provide migration guide

### Phase 3: Remove Legacy Fields (Breaking)

1. Remove `west_manifest` and `scoop_manifest` fields
2. Major version bump

## Benefits

1. **Open/Closed Principle**: Yanga is closed for modification, open for extension
2. **Separation of Concerns**: Yanga brokers configurations; steps interpret them
3. **Uniform Pattern**: All configuration types follow the same collection pattern
4. **Backward Compatible**: Phased migration preserves existing configurations

## Alternatives Considered

### Generic Manifest Dict

```python
manifests: dict[str, Any] = field(default_factory=dict)
```

**Rejected**: Not generic enough. The name "manifests" implies dependency management only. What if you want to configure something else entirely (e.g., code generators, documentation tools)? Also loses the `file` vs inline `content` distinction.

### Plugin-based Manifest Providers

Steps register as manifest providers with parsing callbacks.

**Rejected**: Over-engineered for the problem at hand.

## Open Questions

1. Should `ConfigFile` support a `format` field to hint at file type (yaml, json, toml)?
2. Should there be a `required` field to fail if config is missing?
3. Should configs support environment variable substitution?
