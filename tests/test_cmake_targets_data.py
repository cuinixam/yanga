from pathlib import Path

import pytest

from tests.utils import assert_element_of_type
from yanga.cmake.artifacts_locator import BuildArtifact
from yanga.cmake.cmake_backend import CMakeCustomCommand, CMakeCustomTarget, CMakePath
from yanga.cmake.targets_data import TargetsDataCMakeGenerator
from yanga.domain.config import PlatformConfig
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def targets_data_generator(execution_context: ExecutionContext, output_dir: Path) -> TargetsDataCMakeGenerator:
    execution_context.platform = PlatformConfig(name="arduino")
    return TargetsDataCMakeGenerator(execution_context, output_dir)


def test_generate(targets_data_generator: TargetsDataCMakeGenerator) -> None:
    elements = targets_data_generator.generate()
    assert elements

    # Should generate one custom command and one custom target
    custom_command = assert_element_of_type(elements, CMakeCustomCommand)
    assert custom_command.description == "Generate variant targets data documentation"
    assert custom_command.depends == [targets_data_generator.artifacts_locator.get_build_artifact(BuildArtifact.TARGETS_DATA)]
    output_path = assert_element_of_type(custom_command.outputs, CMakePath)
    assert "targets_data.md" in output_path.to_string()

    custom_target = assert_element_of_type(elements, CMakeCustomTarget)
    assert custom_target.name == "targets_data"
    assert custom_target.description == "Generate targets data report"
    assert custom_target.depends == custom_command.outputs
