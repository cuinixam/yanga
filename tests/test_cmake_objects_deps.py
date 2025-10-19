from pathlib import Path

import pytest

from tests.utils import assert_element_of_type
from yanga.cmake.cmake_backend import CMakeCustomCommand, CMakeCustomTarget
from yanga.cmake.objects_deps import ObjectsDepsCMakeGenerator
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def objects_deps_generator(execution_context: ExecutionContext, output_dir: Path) -> ObjectsDepsCMakeGenerator:
    return ObjectsDepsCMakeGenerator(execution_context, output_dir)


def test_generate(objects_deps_generator: ObjectsDepsCMakeGenerator) -> None:
    elements = objects_deps_generator.generate()
    assert elements

    # Should generate one custom command and one custom target
    custom_command = assert_element_of_type(elements, CMakeCustomCommand)
    assert custom_command.description == "Run clanguru to generate the objects dependencies report"
    assert custom_command.depends == ["compile"]
    assert custom_command.outputs
    assert len(custom_command.outputs) == 1
    output_path = str(custom_command.outputs[0])
    assert "objects_deps.html" in output_path

    custom_target = assert_element_of_type(elements, CMakeCustomTarget)
    assert custom_target.name == "objects_deps"
    assert custom_target.description == "Generate objects dependencies report"
    assert custom_target.depends == custom_command.outputs
