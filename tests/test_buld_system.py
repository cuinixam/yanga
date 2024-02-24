from pathlib import Path
from typing import List, Type, TypeVar
from unittest.mock import Mock, PropertyMock

import pytest

from yanga.domain.execution_context import ExecutionContext
from yanga.ybuild.backends.cmake import (
    CMakeCustomTarget,
    CMakeElement,
    CMakeFile,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeMinimumVersion,
    CMakeObjectLibrary,
    CMakeProject,
)
from yanga.ybuild.generators.build_system import CmakeBuildFilesGenerator

T = TypeVar("T", bound=CMakeElement)


@pytest.fixture
def env() -> ExecutionContext:
    env = Mock()
    env.variant_name = "var1"
    env.components = []
    env.include_directories = []
    env.platform = None
    return env


class CMakeAnalyzer:
    def __init__(self, cmake_file: CMakeFile):
        self.cmake_file = cmake_file

    def find_elements_of_type(self, element_type: Type[T]) -> List[T]:
        return [elem for elem in self.cmake_file.content if isinstance(elem, element_type)]

    def assert_element_of_type(self, element_type: Type[T]) -> T:
        elements = self.find_elements_of_type(element_type)
        assert elements, f"No element of type {element_type.__name__} found"
        assert len(elements) == 1, f"More than one element of type {element_type.__name__} found"
        return elements[0]

    def assert_elements_of_type(self, element_type: Type[T], count: int) -> List[T]:
        elements = self.find_elements_of_type(element_type)
        assert (
            len(elements) == count
        ), f"Expected {count} elements of type {element_type.__name__}, found {len(elements)}"
        return elements


def test_generate_method(env: ExecutionContext, tmp_path: Path) -> None:
    generator = CmakeBuildFilesGenerator(env, tmp_path)
    generated_files = generator.generate()

    for file in generated_files:
        file.to_file()
    for filename in ["CMakeLists.txt", "variant.cmake", "components.cmake"]:
        assert (tmp_path / filename).exists(), f"File {filename} shall be generated"


def test_cmake_build_cmakelists_file(env: ExecutionContext) -> None:
    generator = CmakeBuildFilesGenerator(env, Path("/test/output/dir"))
    generated_files = generator.generate()

    cmakelists_file = generated_files[0]
    assert cmakelists_file.path.name == "CMakeLists.txt"
    cmakelists_analyzer = CMakeAnalyzer(cmakelists_file)
    assert cmakelists_analyzer.assert_element_of_type(CMakeMinimumVersion).version == "3.20"
    assert cmakelists_analyzer.assert_element_of_type(CMakeProject).name == "var1"
    assert "variant.cmake" in cmakelists_analyzer.assert_element_of_type(CMakeInclude).to_string()


def test_cmake_build_variant_file(env: ExecutionContext) -> None:
    artifacts_locator = Mock()
    artifacts_locator.locate_artifact = lambda artifact, _: Path(f"/some/path/{artifact}")
    env.create_artifacts_locator = lambda: artifacts_locator  # type: ignore
    component = Mock()
    component.path = Path("/some/path")
    component.sources = ["src/source1", "test/source2"]
    env.components = [component]
    # Mock the include_directories property
    include_dirs = [Path("/gen/include/dir1")]
    type(env).include_directories = PropertyMock(return_value=include_dirs)  # type: ignore
    variant_file = CmakeBuildFilesGenerator(env, Path("/test/output/dir")).create_variants_cmake()
    assert variant_file.path.name == "variant.cmake"
    variant_analyzer = CMakeAnalyzer(variant_file)
    assert "components.cmake" in variant_analyzer.assert_element_of_type(CMakeInclude).to_string()
    assert len(variant_analyzer.assert_element_of_type(CMakeIncludeDirectories).paths) == 3, "two components + gen dir"


def test_cmake_build_components_file(env: ExecutionContext) -> None:
    component1 = Mock()
    component1.path = Path("/some/path")
    component1.sources = ["src/source1", "test/source2"]
    component2 = Mock()
    component2.path = Path("/some/path2")
    component2.sources = ["src/source3", "test/source4"]
    env.components = [component1, component2]
    components_file = CmakeBuildFilesGenerator(env, Path("/test/output/dir")).create_components_cmake()
    assert components_file.path.name == "components.cmake"
    components_analyzer = CMakeAnalyzer(components_file)
    assert components_analyzer.assert_elements_of_type(CMakeObjectLibrary, 2)
    assert components_analyzer.assert_elements_of_type(CMakeCustomTarget, 4), "_lib and _compile for both components"
