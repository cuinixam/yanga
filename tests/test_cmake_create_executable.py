from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.utils import CMakeAnalyzer
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeCustomTarget,
    CMakeObjectLibrary,
)
from yanga.cmake.create_executable import CreateExecutableCMakeGenerator
from yanga.domain.components import Component, ComponentType
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def env() -> ExecutionContext:
    env = Mock(spec=ExecutionContext)
    env.variant_name = "mock_variant"
    env.components = [
        Component(
            name="CompA",
            type=ComponentType.COMPONENT,
            path=Path("compA"),
            sources=["srcA/source.cpp"],
            test_sources=["test_source.cpp"],
            include_dirs=[],
            is_subcomponent=False,
            description="Mock component A",
            components=[],
        ),
        Component(
            name="CompBNotTestable",
            type=ComponentType.COMPONENT,
            path=Path("compB"),
            sources=["srcB/source.cpp"],
            test_sources=[],
            include_dirs=[],
            is_subcomponent=False,
            description="Mock component A",
            components=[],
        ),
    ]
    env.include_directories = [Path("/mock/include/dir")]
    artifacts_locator = Mock()
    artifacts_locator.locate_artifact = lambda artifact, _: Path(f"/some/path/{artifact}")
    env.create_artifacts_locator = lambda: artifacts_locator
    return env


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def create_executable_generator(env: ExecutionContext, output_dir: Path) -> CreateExecutableCMakeGenerator:
    return CreateExecutableCMakeGenerator(env, output_dir)


def test_generate(create_executable_generator: CreateExecutableCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements
    cmake_analyzer = CMakeAnalyzer(elements)
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert executable.name == "${PROJECT_NAME}"
    targets = cmake_analyzer.assert_elements_of_type(CMakeCustomTarget, 5)
    assert [target.name for target in targets] == [
        "build",
        "CompA_compile",
        "CompA_build",
        "CompBNotTestable_compile",
        "CompBNotTestable_build",
    ]


def test_create_variant_cmake_elements(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_variant_cmake_elements()
    cmake_analyzer = CMakeAnalyzer(elements)
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert executable.name == "${PROJECT_NAME}"
    custom_target = cmake_analyzer.assert_element_of_type(CMakeCustomTarget)
    assert custom_target.name == "build"


def test_get_include_directories(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    assert len(create_executable_generator.get_include_directories().paths) == 3  # Two from components, one global


def test_create_components_cmake_elements(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()
    cmake_analyzer = CMakeAnalyzer(elements)
    object_libraries = cmake_analyzer.find_elements_of_type(CMakeObjectLibrary)
    assert len(object_libraries) == 2  # One for each component
    compile_targets = cmake_analyzer.find_elements_of_type(CMakeCustomTarget)
    assert [target.name for target in compile_targets] == [
        "CompA_compile",
        "CompA_build",
        "CompBNotTestable_compile",
        "CompBNotTestable_build",
    ]
