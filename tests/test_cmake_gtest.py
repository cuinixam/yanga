from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.utils import CMakeAnalyzer
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeCustomTarget,
    CMakeInclude,
    CMakeVariable,
)
from yanga.cmake.gtest import GTestCMakeGenerator
from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.components import Component, ComponentType
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def locate_artifact():
    """Fixture to mock the locate_artifact method."""
    with patch(
        ProjectArtifactsLocator.__module__ + "." + ProjectArtifactsLocator.__name__ + ".locate_artifact",
        side_effect=lambda file, _: Path(file),
    ) as my_locate_artifact:
        yield my_locate_artifact


@pytest.fixture
def env(locate_artifact: Mock) -> ExecutionContext:
    env = Mock(spec=ExecutionContext)
    env.variant_name = "mock_variant"
    env.components = [
        Component(
            name="CompA",
            type=ComponentType.COMPONENT,
            path=Path("compA"),
            sources=["source.cpp"],
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
            sources=["source.cpp"],
            test_sources=[],
            include_dirs=[],
            is_subcomponent=False,
            description="Mock component A",
            components=[],
        ),
    ]
    env.include_directories = [Path("/mock/include/dir")]
    env.create_artifacts_locator.return_value = ProjectArtifactsLocator(Path("/mock/project/root"), "mock_variant", "mock_platform")
    return env


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def gtest_cmake_generator(env: ExecutionContext, output_dir: Path) -> GTestCMakeGenerator:
    return GTestCMakeGenerator(env, output_dir)


def test_generate(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    elements = gtest_cmake_generator.generate()
    assert elements
    cmake_analyzer = CMakeAnalyzer(elements)
    variables = cmake_analyzer.assert_elements_of_type(CMakeVariable, 4)
    assert [var.name for var in variables] == ["CMAKE_CXX_STANDARD", "CMAKE_CXX_STANDARD_REQUIRED", "gtest_force_shared_crt", "CMAKE_BUILD_DIR"]
    includes = cmake_analyzer.assert_elements_of_type(CMakeInclude, 2)
    assert [include.path for include in includes] == ["GoogleTest", "CTest"]


def test_create_variant_cmake_elements(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_variant_cmake_elements()
    assert elements


def test_cmake_build_components_file(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_components_cmake_elements()
    cmake_analyzer = CMakeAnalyzer(elements)
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert executable.name == "CompA"
    targets = cmake_analyzer.assert_elements_of_type(CMakeCustomTarget, 3)
    assert [target.name for target in targets] == ["CompA_mockup", "CompA_test", "CompA_build"]


def test_get_include_directories(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    assert len(gtest_cmake_generator.get_include_directories().paths) == 5
