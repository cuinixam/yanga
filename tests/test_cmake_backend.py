from pathlib import Path

from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeAddSubdirectory,
    CMakeCommand,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeEnableTesting,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeLibrary,
    CMakeListAppend,
    CMakeMinimumVersion,
    CMakeObjectLibrary,
    CMakePath,
    CMakeProject,
    CMakeTargetIncludeDirectories,
    CMakeVariable,
)
from yanga.cmake.generator import CMakeFile


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


# Let's extend the tests to cover all features of the provided CMake classes.


def test_cmake_library():
    files = [Path("lib1.cpp"), Path("lib2.cpp")]
    cmake_library = CMakeLibrary("test", files)
    assert cmake_library.to_string() == "add_library(test_lib OBJECT lib1.cpp lib2.cpp)"


def test_cmake_library_with_compile_options():
    files = [Path("lib1.cpp"), Path("lib2.cpp")]
    compile_options = ["-ggdb", "--coverage"]
    cmake_library = CMakeLibrary("test", files, compile_options=compile_options)
    expected = "add_library(test_lib OBJECT lib1.cpp lib2.cpp)\ntarget_compile_options(test_lib PRIVATE -ggdb --coverage)"
    assert cmake_library.to_string() == expected


def test_cmake_object_library():
    files = [Path("obj1.cpp"), Path("obj2.cpp")]
    cmake_object_library = CMakeObjectLibrary("obj", files)
    assert cmake_object_library.to_string() == "add_library(obj_lib OBJECT obj1.cpp obj2.cpp)"


def test_cmake_object_library_with_compile_options():
    files = [Path("obj1.cpp"), Path("obj2.cpp")]
    compile_options = ["-O2", "-Wall"]
    cmake_object_library = CMakeObjectLibrary("obj", files, compile_options=compile_options)
    expected = "add_library(obj_lib OBJECT obj1.cpp obj2.cpp)\ntarget_compile_options(obj_lib PRIVATE -O2 -Wall)"
    assert cmake_object_library.to_string() == expected


def test_cmake_path():
    path = Path("/usr/local/test")
    cmake_path = CMakePath(path)
    assert str(cmake_path) == "/usr/local/test"
    cmake_path_with_variable = CMakePath(path, "TEST_PATH")
    assert str(cmake_path_with_variable) == "${TEST_PATH}"
    cmake_path_joined = cmake_path_with_variable.joinpath("include")
    assert str(cmake_path_joined) == "${TEST_PATH}/include"
    # Use joinpath multiple times
    assert cmake_path_joined.joinpath("comp").to_path() == path / "include" / "comp"
    # Create file with suffix
    assert CMakePath(Path("some/file.txt")).with_suffix(".md").to_path() == Path("some/file.md")


def test_cmake_include():
    cmake_include = CMakeInclude("TestInclude.cmake")
    assert cmake_include.to_string() == "include(TestInclude.cmake)"
    cmake_include_path = CMakeInclude(CMakePath(Path("root/path"), "INCLUDE_PATH", Path("extra/dir")))
    assert cmake_include_path.to_string() == "include(${INCLUDE_PATH}/extra/dir)"
    assert isinstance(cmake_include_path.path, CMakePath)
    assert cmake_include_path.path.to_path() == Path("root/path/extra/dir")


def test_cmake_include_directories():
    paths = [CMakePath(Path("/include/dir1")), CMakePath(Path("/include/dir2"))]
    cmake_include_directories = CMakeIncludeDirectories(paths)
    assert cmake_include_directories.to_string() == "include_directories(\n    /include/dir1\n    /include/dir2\n)"


def test_cmake_add_subdirectory():
    source_dir = CMakePath(Path("src"))
    cmake_add_subdirectory = CMakeAddSubdirectory(source_dir)
    assert cmake_add_subdirectory.to_string() == "add_subdirectory(src)"


def test_cmake_custom_command():
    outputs = [CMakePath(Path("output1")), CMakePath(Path("output2"))]
    depends: list[str | CMakePath] = ["input1", "input2"]
    commands = [CMakeCommand("my_command", ["arg1", "arg2"])]
    cmake_custom_command = CMakeCustomCommand("Generate outputs", outputs, depends, commands)
    expected_string = "# Generate outputs\nadd_custom_command(\n    OUTPUT output1 output2\n    DEPENDS input1 input2\n    COMMAND my_command arg1 arg2\n)"
    assert cmake_custom_command.to_string() == expected_string


def test_cmake_custom_target():
    commands = [CMakeCommand("my_target_command", ["arg1", "arg2"])]
    cmake_custom_target = CMakeCustomTarget("my_custom_target", "Build custom target", commands, ["depend1"], True, [CMakePath(Path("output1.txt"))])
    expected_string = "# Build custom target\nadd_custom_target(my_custom_target ALL\n    COMMAND my_target_command arg1 arg2\n    DEPENDS depend1\n    BYPRODUCTS output1.txt\n)"
    assert cmake_custom_target.to_string() == expected_string


def test_cmake_file():
    cmake_file = CMakeFile(Path("CMakeLists.txt"))
    cmake_file.append(CMakeProject("TestProject"))
    cmake_file.append(CMakeMinimumVersion("3.15"))
    expected_string = "project(TestProject)\ncmake_minimum_required(VERSION 3.15)"
    assert cmake_file.to_string() == expected_string


def test_cmake_list_append():
    cmake_list_append = CMakeListAppend("MY_LIST", ["value1", "value2"])
    assert cmake_list_append.to_string() == "list(APPEND MY_LIST value1 value2)"


def test_cmake_enable_testing():
    cmake_enable_testing = CMakeEnableTesting()
    assert cmake_enable_testing.to_string() == "enable_testing()"


def test_cmake_target_include_directories():
    paths = [CMakePath(Path("/include/dir1")), CMakePath(Path("/include/dir2"))]
    target_include_dirs = CMakeTargetIncludeDirectories("my_target", paths, "PRIVATE")
    assert target_include_dirs.to_string() == "target_include_directories(my_target PRIVATE /include/dir1 /include/dir2)"

    # Test with INTERFACE visibility
    interface_include_dirs = CMakeTargetIncludeDirectories("my_interface", paths, "INTERFACE")
    assert interface_include_dirs.to_string() == "target_include_directories(my_interface INTERFACE /include/dir1 /include/dir2)"

    # Test with empty paths
    empty_include_dirs = CMakeTargetIncludeDirectories("my_target", [], "PRIVATE")
    assert empty_include_dirs.to_string() == ""
