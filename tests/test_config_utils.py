from dataclasses import dataclass
from pathlib import Path

from yanga.domain.config import ConfigFile, PlatformConfig, VariantConfig, VariantPlatformsConfig
from yanga.domain.config_utils import collect_configs_by_id, parse_config
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest


def test_collect_configs_with_no_configs(tmp_path: Path) -> None:
    context = ExecutionContext(project_root_dir=tmp_path, variant_name="test", user_request=UserVariantRequest("test"))
    configs = collect_configs_by_id(context, "west")
    assert configs == []


def test_collect_configs_from_variant(tmp_path: Path) -> None:
    variant = VariantConfig(name="test", configs=[ConfigFile(id="west", content={"key": "variant"})])
    context = ExecutionContext(project_root_dir=tmp_path, variant_name="test", user_request=UserVariantRequest("test"), variant=variant)
    configs = collect_configs_by_id(context, "west")
    assert len(configs) == 1
    assert configs[0].content == {"key": "variant"}


def test_collect_configs_from_platform(tmp_path: Path) -> None:
    platform = PlatformConfig(name="linux", configs=[ConfigFile(id="west", content={"key": "platform"})])
    context = ExecutionContext(project_root_dir=tmp_path, variant_name="test", user_request=UserVariantRequest("test"), platform=platform)
    configs = collect_configs_by_id(context, "west")
    assert len(configs) == 1
    assert configs[0].content == {"key": "platform"}


def test_collect_configs_order_variant_then_platform(tmp_path: Path) -> None:
    variant = VariantConfig(name="test", configs=[ConfigFile(id="west", content={"key": "variant"})])
    platform = PlatformConfig(name="linux", configs=[ConfigFile(id="west", content={"key": "platform"})])
    context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test",
        user_request=UserVariantRequest("test"),
        variant=variant,
        platform=platform,
    )
    configs = collect_configs_by_id(context, "west")
    assert len(configs) == 2
    assert configs[0].content == {"key": "variant"}
    assert configs[1].content == {"key": "platform"}


def test_collect_configs_from_variant_platform(tmp_path: Path) -> None:
    platform = PlatformConfig(name="linux")
    variant = VariantConfig(
        name="test",
        platforms={"linux": VariantPlatformsConfig(configs=[ConfigFile(id="west", content={"key": "vp"})])},
    )
    context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test",
        user_request=UserVariantRequest("test"),
        variant=variant,
        platform=platform,
    )
    configs = collect_configs_by_id(context, "west")
    assert len(configs) == 1
    assert configs[0].content == {"key": "vp"}


def test_collect_configs_filters_by_id(tmp_path: Path) -> None:
    variant = VariantConfig(
        name="test",
        configs=[ConfigFile(id="west", content={"type": "west"}), ConfigFile(id="scoop", content={"type": "scoop"})],
    )
    context = ExecutionContext(project_root_dir=tmp_path, variant_name="test", user_request=UserVariantRequest("test"), variant=variant)
    west_configs = collect_configs_by_id(context, "west")
    assert len(west_configs) == 1
    assert west_configs[0].content == {"type": "west"}

    scoop_configs = collect_configs_by_id(context, "scoop")
    assert len(scoop_configs) == 1
    assert scoop_configs[0].content == {"type": "scoop"}


@dataclass
class MockConfig:
    data: dict

    @classmethod
    def from_dict(cls, data: dict) -> "MockConfig":
        return cls(data=data)

    @classmethod
    def from_file(cls, path: Path) -> "MockConfig":
        import json

        return cls(data=json.loads(path.read_text()))


def test_parse_config_from_content() -> None:
    config = ConfigFile(id="test", content={"key": "value"})
    result = parse_config(config, MockConfig)
    assert result.data == {"key": "value"}


def test_parse_config_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"loaded": "from_file"}')
    config = ConfigFile(id="test", file=config_file)
    result = parse_config(config, MockConfig)
    assert result.data == {"loaded": "from_file"}


def test_parse_config_with_base_path(tmp_path: Path) -> None:
    config_file = tmp_path / "subdir" / "config.json"
    config_file.parent.mkdir()
    config_file.write_text('{"loaded": "with_base_path"}')
    config = ConfigFile(id="test", file=Path("subdir/config.json"))
    result = parse_config(config, MockConfig, base_path=tmp_path)
    assert result.data == {"loaded": "with_base_path"}


def test_parse_config_prefers_content_over_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"loaded": "from_file"}')
    config = ConfigFile(id="test", file=config_file, content={"loaded": "from_content"})
    result = parse_config(config, MockConfig)
    assert result.data == {"loaded": "from_content"}
