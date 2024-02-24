from pathlib import Path

from yanga.ybuild.backends.cmake import (
    CMakeAddExecutable,
    CMakeLists,
    CMakePath,
    CMakeVariable,
)


def test_cmakelists_to_string():
    path = Path("some_path/CMakeLists.txt")
    cmakelists = CMakeLists(path)
    cmakelists.project_name = "TestProject"
    cmakelists.cmake_version = "3.20"

    expected_content = ["cmake_minimum_required(VERSION 3.20)", "project(TestProject)"]
    content = cmakelists.to_string()
    for line in expected_content:
        assert line in content


def test_cmake_variable():
    cmake_variable = CMakeVariable("test_var", "test_value")
    assert cmake_variable.to_string() == "set(test_var test_value)"
    cmake_variable = CMakeVariable("gtest_force_shared_crt", "ON", True, "BOOL", "", True)
    assert cmake_variable.to_string() == 'set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)'


def test_cmake_executable():
    cmake_executable = CMakeAddExecutable(
        "test_executable",
        [CMakePath(Path(source)) for source in ["test1.cpp", "test2.cpp"]],
        ["GTest::gtest_main"],
        [
            "-ggdb",  # Include detailed debug information to be able to debug the executable.
            "--coverage",  # Enable coverage tracking information to be generated.
        ],
        ["--coverage"],  # Enable coverage analysis.
    )
    assert cmake_executable.to_string() == (
        "add_executable(test_executable test1.cpp test2.cpp)\n"
        "target_link_libraries(test_executable GTest::gtest_main)\n"
        "target_compile_options(test_executable PRIVATE -ggdb --coverage)\n"
        "target_link_options(test_executable PRIVATE --coverage)"
    )
