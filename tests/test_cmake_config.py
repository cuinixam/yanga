from pathlib import Path
from tempfile import TemporaryDirectory

from tests.utils import assert_elements_of_type
from yanga.cmake.cmake_backend import CMakeComment, CMakeVariable
from yanga.cmake.variant_config import ConfigCMakeGenerator
from yanga.domain.config import VariantConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest


def test_config_cmake_generator_with_no_config() -> None:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        execution_context = ExecutionContext(
            project_root_dir=Path(temp_dir),
            user_request=UserVariantRequest("test_variant"),
            variant_name="test_variant",
        )

        generator = ConfigCMakeGenerator(execution_context, output_dir)
        elements = generator.generate()

        # Should only contain the generator comment
        assert len(elements) == 1
        assert isinstance(elements[0], CMakeComment)
        assert "ConfigCMakeGenerator" in elements[0].to_string()


def test_config_cmake_generator_with_variant_config() -> None:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        variant = VariantConfig(
            name="test_variant",
            config={
                "LINKER_SCRIPT": "STM32F103.ld",
                "GREETING": "Hallo, Welt!",
                "DEBUG_LEVEL": "2",
                "ENABLE_FEATURE": "ON",
            },
        )

        execution_context = ExecutionContext(
            project_root_dir=Path(temp_dir),
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
        assert "Variant-specific configuration variables" in comments[1].to_string()

        # Check the variables
        variables = assert_elements_of_type(elements, CMakeVariable, 4)
        variable_dict = {var.name: var.value for var in variables}

        assert variable_dict["LINKER_SCRIPT"] == "STM32F103.ld"
        assert variable_dict["GREETING"] == "Hallo, Welt!"
        assert variable_dict["DEBUG_LEVEL"] == "2"
        assert variable_dict["ENABLE_FEATURE"] == "ON"


def test_config_cmake_generator_with_empty_config() -> None:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        variant = VariantConfig(name="test_variant", config={})

        execution_context = ExecutionContext(
            project_root_dir=Path(temp_dir),
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
