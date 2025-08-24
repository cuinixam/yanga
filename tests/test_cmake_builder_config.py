from pathlib import Path
from tempfile import TemporaryDirectory

from tests.utils import CMakeAnalyzer
from yanga.cmake.builder import CMakeBuildSystemGenerator
from yanga.cmake.cmake_backend import CMakeComment, CMakeVariable
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

        # Should generate both config.cmake and variant.cmake files
        assert len(files) == 2

        # Find the config.cmake file
        config_file = next((f for f in files if f.path.name == "config.cmake"), None)
        assert config_file is not None

        # Analyze the config.cmake content
        cmake_analyzer = CMakeAnalyzer(config_file.content)

        # Check for comments and variables
        comments = cmake_analyzer.assert_elements_of_type(CMakeComment, 2)
        assert "ConfigCMakeGenerator" in comments[0].to_string()
        assert "Variant-specific configuration variables" in comments[1].to_string()

        variables = cmake_analyzer.assert_elements_of_type(CMakeVariable, 3)
        variable_dict = {var.name: var.value for var in variables}

        assert variable_dict["LINKER_SCRIPT"] == "STM32F407.ld"
        assert variable_dict["MCU_FAMILY"] == "STM32F4"
        assert variable_dict["HEAP_SIZE"] == "32768"


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

        # Should generate both config.cmake and variant.cmake files
        assert len(files) == 2

        # Find the config.cmake file
        config_file = next((f for f in files if f.path.name == "config.cmake"), None)
        assert config_file is not None

        # Analyze the config.cmake content
        cmake_analyzer = CMakeAnalyzer(config_file.content)

        # Should only have the generator comment
        comments = cmake_analyzer.assert_elements_of_type(CMakeComment, 1)
        assert "ConfigCMakeGenerator" in comments[0].to_string()

        # Should have no variables
        variables = cmake_analyzer.find_elements_of_type(CMakeVariable)
        assert len(variables) == 0
