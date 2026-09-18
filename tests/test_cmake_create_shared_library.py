from pathlib import Path

from yanga_core.domain.execution_context import ExecutionContext

from tests.utils import find_elements_of_type
from yanga.cmake.cmake_backend import CMakeAddExecutable, CMakeAddLibrary, CMakeCustomTarget, CMakeSetTargetProperties, CMakeTargetLinkLibraries, LibraryType
from yanga.cmake.create_shared_library import CreateSharedLibraryCMakeGenerator


def test_variant_is_linked_into_a_shared_library_named_like_the_executable(execution_context: ExecutionContext, output_dir: Path) -> None:
    elements = CreateSharedLibraryCMakeGenerator(execution_context, output_dir).generate()

    assert not find_elements_of_type(elements, CMakeAddExecutable)
    shared = next(library for library in find_elements_of_type(elements, CMakeAddLibrary) if library.type is LibraryType.SHARED)
    assert shared.to_string() == "add_library(${PROJECT_NAME}_lib SHARED )"
    assert find_elements_of_type(elements, CMakeTargetLinkLibraries)[0].to_string() == "target_link_libraries(${PROJECT_NAME}_lib CompA_lib CompBNotTestable_lib)"
    properties = find_elements_of_type(elements, CMakeSetTargetProperties)[0]
    assert properties.target == "${PROJECT_NAME}_lib"
    assert properties.properties == {"OUTPUT_NAME": "${PROJECT_NAME}", "PREFIX": '""', "WINDOWS_EXPORT_ALL_SYMBOLS": "ON"}
    build_target = next(target for target in find_elements_of_type(elements, CMakeCustomTarget) if target.name == "build")
    assert build_target.depends == ["${PROJECT_NAME}_lib"]
