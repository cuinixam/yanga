import sys
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast

from yanga.domain.config import ConfigFile
from yanga.domain.execution_context import ExecutionContext

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class ConfigPrototype(Protocol):
    """Protocol for config classes that support from_dict and from_file."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self: ...

    @classmethod
    def from_file(cls, path: Path) -> Self: ...


T = TypeVar("T", bound=ConfigPrototype)


def collect_configs_by_id(context: ExecutionContext, config_id: str) -> list[ConfigFile]:
    """Collect configs matching id. Order: project → variant → platform → variant-platform."""
    configs: list[ConfigFile] = []

    # 1. Project configs (source_file already stamped by YangaProjectSlurper.project_configs)
    configs.extend(cfg for cfg in context.project_configs if cfg.id == config_id)

    # 2. Variant configs
    if context.variant:
        for cfg in context.variant.configs:
            if cfg.id == config_id:
                cfg.source_file = context.variant.file
                configs.append(cfg)

    # 3. Platform configs
    if context.platform:
        for cfg in context.platform.configs:
            if cfg.id == config_id:
                cfg.source_file = context.platform.file
                configs.append(cfg)

    # 4. Variant-Platform configs (VariantPlatformsConfig has no .file, use variant's)
    if context.variant and context.platform and context.variant.platforms:
        if context.platform.name in context.variant.platforms:
            vp_config = context.variant.platforms[context.platform.name]
            for cfg in vp_config.configs:
                if cfg.id == config_id:
                    cfg.source_file = context.variant.file
                    configs.append(cfg)

    return configs


def parse_config(config: ConfigFile, prototype: type[T], base_path: Path | None = None) -> T:
    """
    Parse ConfigFile using prototype's from_dict or from_file.

        File resolution order for relative paths:
    1. Relative to the declaring yanga.yaml (source_file.parent), if source_file is set and the file exists there
    2. Relative to base_path (typically project root), as fallback
    """
    if config.content:
        return cast(T, prototype.from_dict(config.content))
    if config.file:
        if config.source_file and not Path(config.file).is_absolute():
            candidate = config.source_file.parent / config.file
            if candidate.exists():
                return cast(T, prototype.from_file(candidate))
        file_path = base_path / config.file if base_path else config.file
        return cast(T, prototype.from_file(file_path))
    raise ValueError(f"ConfigFile '{config.id}' has neither file nor content")
