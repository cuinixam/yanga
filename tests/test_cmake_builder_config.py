from pathlib import Path
from tempfile import TemporaryDirectory

from tests.utils import assert_element_of_type, assert_elements_of_type
from yanga.cmake.builder import CMakeBuildSystemGenerator
from yanga.cmake.cmake_backend import CMakeComment, CMakeVariable
from yanga.cmake.generator import CMakeFile
from yanga.domain.config import VariantConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest


def test_cmake_build_system_generator_creates_config_file() -> None:
    """Test that CMakeBuildSystemGenerator creates a config.cmake file with variant configuration."""
    with TemporaryDirectory() as temp_dir:
        project_root_dir = Path(temp_dir)
        output_dir = project_root_dir / "output"

        variant = VariantConfig(
            name="test_variant",
            config={
                "LINKER_SCRIPT": "STM32F407.ld",
                "MCU_FAMILY": "STM32F4",
                "HEAP_SIZE": "32768",
            },
        )

        execution_context = ExecutionContext(
            project_root_dir=project_root_dir,
            user_request=UserVariantRequest("test_variant"),
            variant_name="test_variant",
            variant=variant,
        )

        generator = CMakeBuildSystemGenerator(execution_context, output_dir)
        files = generator.generate()

        assert len(files) == 4

        # Find the config.cmake file
        config_file = assert_element_of_type(files, CMakeFile, lambda f: f.path.as_posix().endswith("config.cmake"))

        # Check for comments and variables
        comments = assert_elements_of_type(config_file.content, CMakeComment, 2)
        assert "ConfigCMakeGenerator" in comments[0].to_string()
        assert "Variant-specific configuration variables" in comments[1].to_string()

        variables = assert_elements_of_type(config_file.content, CMakeVariable, 4)
        assert {
            "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
            "LINKER_SCRIPT": "STM32F407.ld",
            "MCU_FAMILY": "STM32F4",
            "HEAP_SIZE": "32768",
        } == {var.name: var.value for var in variables}


def test_cmake_build_system_generator_creates_empty_config_file() -> None:
    """Test that CMakeBuildSystemGenerator creates an empty config.cmake file when no variant config exists."""
    with TemporaryDirectory() as temp_dir:
        project_root_dir = Path(temp_dir)
        output_dir = project_root_dir / "output"

        execution_context = ExecutionContext(
            project_root_dir=project_root_dir,
            user_request=UserVariantRequest("test_variant"),
            variant_name="test_variant",
        )

        generator = CMakeBuildSystemGenerator(execution_context, output_dir)
        files = generator.generate()

        assert len(files) == 4

        # Find the config.cmake file
        config_file = assert_element_of_type(files, CMakeFile, lambda f: f.path.as_posix().endswith("config.cmake"))

        # Should only have the generator comment
        assert "ConfigCMakeGenerator" in assert_element_of_type(config_file.content, CMakeComment).to_string()

        # Should have no variables
        variable = assert_element_of_type(config_file.content, CMakeVariable)
        assert variable.name == "CMAKE_EXPORT_COMPILE_COMMANDS"
