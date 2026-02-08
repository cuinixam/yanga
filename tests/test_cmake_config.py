from pathlib import Path

from tests.utils import assert_elements_of_type
from yanga.cmake.cmake_backend import CMakeComment, CMakeVariable
from yanga.cmake.variant_config import ConfigCMakeGenerator
from yanga.domain.config import ConfigFile, PlatformConfig, VariantConfig, VariantPlatformsConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest


def test_config_cmake_generator_with_no_config(tmp_path: Path) -> None:
    output_dir = tmp_path
    execution_context = ExecutionContext(
        project_root_dir=output_dir,
        user_request=UserVariantRequest("test_variant"),
        variant_name="test_variant",
    )

    generator = ConfigCMakeGenerator(execution_context, output_dir)
    elements = generator.generate()

    # Should only contain the generator comment
    assert len(elements) == 1
    assert isinstance(elements[0], CMakeComment)
    assert "ConfigCMakeGenerator" in elements[0].to_string()


def test_config_cmake_generator_with_variant_config(tmp_path: Path) -> None:
    output_dir = tmp_path
    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="vars",
                content={
                    "LINKER_SCRIPT": "STM32F103.ld",
                    "GREETING": "Hallo, Welt!",
                    "DEBUG_LEVEL": "2",
                    "ENABLE_FEATURE": "ON",
                },
            )
        ],
    )

    execution_context = ExecutionContext(
        project_root_dir=output_dir,
        user_request=UserVariantRequest("test_variant"),
        variant_name="test_variant",
        variant=variant,
    )

    generator = ConfigCMakeGenerator(execution_context, output_dir)
    elements = generator.generate()

    # Should contain generator comment + configuration comment + 4 variables
    assert len(elements) == 6

    # Check the comments
    comments = assert_elements_of_type(elements, CMakeComment, 2)
    assert "ConfigCMakeGenerator" in comments[0].to_string()
    assert "Configuration variables" in comments[1].to_string()

    # Check the variables
    variables = assert_elements_of_type(elements, CMakeVariable, 4)
    variable_dict = {var.name: var.value for var in variables}

    assert variable_dict["LINKER_SCRIPT"] == "STM32F103.ld"
    assert variable_dict["GREETING"] == "Hallo, Welt!"
    assert variable_dict["DEBUG_LEVEL"] == "2"
    assert variable_dict["ENABLE_FEATURE"] == "ON"


def test_config_cmake_generator_with_empty_config(tmp_path: Path) -> None:
    output_dir = tmp_path
    variant = VariantConfig(name="test_variant", configs=[])

    execution_context = ExecutionContext(
        project_root_dir=output_dir,
        user_request=UserVariantRequest("test_variant"),
        variant_name="test_variant",
        variant=variant,
    )

    generator = ConfigCMakeGenerator(execution_context, output_dir)
    elements = generator.generate()

    # Should only contain the generator comment
    assert len(elements) == 1
    assert isinstance(elements[0], CMakeComment)
    assert "ConfigCMakeGenerator" in elements[0].to_string()


def test_config_cmake_generator_with_platform_specific_config(tmp_path: Path) -> None:
    output_dir = tmp_path

    # Create platform config
    platform = PlatformConfig(name="test_platform")

    # Create variant with platform-specific config using configs with id="vars"
    variant = VariantConfig(
        name="test_variant",
        configs=[ConfigFile(id="vars", content={"BASE_CONFIG": "base_value"})],
        platforms={
            "test_platform": VariantPlatformsConfig(
                components=["platform_component"],
                configs=[ConfigFile(id="vars", content={"PLATFORM_CONFIG": "platform_value", "OVERRIDE_CONFIG": "override_value"})],
            )
        },
    )

    execution_context = ExecutionContext(
        project_root_dir=output_dir,
        user_request=UserVariantRequest("test_variant"),
        variant_name="test_variant",
        variant=variant,
        platform=platform,
    )

    generator = ConfigCMakeGenerator(execution_context, output_dir)
    elements = generator.generate()

    # Should contain generator comment + config comment + 3 variables (all configs merged)
    assert len(elements) == 5

    # Check the comments
    comments = assert_elements_of_type(elements, CMakeComment, 2)
    assert "ConfigCMakeGenerator" in comments[0].to_string()
    assert "Configuration variables" in comments[1].to_string()

    # Check the variables
    variables = assert_elements_of_type(elements, CMakeVariable, 3)
    variable_dict = {var.name: var.value for var in variables}

    assert variable_dict["BASE_CONFIG"] == "base_value"
    assert variable_dict["PLATFORM_CONFIG"] == "platform_value"
    assert variable_dict["OVERRIDE_CONFIG"] == "override_value"


def test_config_cmake_generator_with_platform_no_specific_config(tmp_path: Path) -> None:
    output_dir = tmp_path

    # Create platform config
    platform = PlatformConfig(name="test_platform")

    # Create variant with platform-specific config for a different platform
    variant = VariantConfig(
        name="test_variant",
        configs=[ConfigFile(id="vars", content={"BASE_CONFIG": "base_value"})],
        platforms={"other_platform": VariantPlatformsConfig(configs=[ConfigFile(id="vars", content={"OTHER_CONFIG": "other_value"})])},
    )

    execution_context = ExecutionContext(
        project_root_dir=output_dir,
        user_request=UserVariantRequest("test_variant"),
        variant_name="test_variant",
        variant=variant,
        platform=platform,
    )

    generator = ConfigCMakeGenerator(execution_context, output_dir)
    elements = generator.generate()

    # Should contain generator comment + config comment + 1 base variable (no platform-specific config)
    assert len(elements) == 3

    # Check the comments
    comments = assert_elements_of_type(elements, CMakeComment, 2)
    assert "ConfigCMakeGenerator" in comments[0].to_string()
    assert "Configuration variables" in comments[1].to_string()

    # Check the variables
    variables = assert_elements_of_type(elements, CMakeVariable, 1)
    assert variables[0].name == "BASE_CONFIG"
    assert variables[0].value == "base_value"
