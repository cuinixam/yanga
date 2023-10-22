from pathlib import Path

from yanga.ybuild.backends.cmake import CMakeLists, CMakeListsBuilder


def test_cmakelists_to_string():
    path = Path("some_path/CMakeLists.txt")
    cmakelists = CMakeLists(path)
    cmakelists.project_name = "TestProject"
    cmakelists.cmake_version = "3.20"

    expected_content = ["cmake_minimum_required(VERSION 3.20)", "project(TestProject)"]
    content = cmakelists.to_string()
    for line in expected_content:
        assert line in content


def test_cmakelistsbuilder_initialization():
    output_path = Path("output_path")
    builder = CMakeListsBuilder(output_path)

    assert builder.output_path == output_path
    assert builder.cmake_lists.path == output_path.joinpath(CMakeListsBuilder.file_name)
    assert builder.cmake_lists.cmake_version == "3.20"


def test_cmakelistsbuilder_with_project_name(tmp_path: Path) -> None:
    output_path = tmp_path
    builder = CMakeListsBuilder(output_path, "13").with_project_name("MyProject")
    expected_content = ["cmake_minimum_required(VERSION 13)", "project(MyProject)"]

    builder.build().to_file()

    content = output_path.joinpath("CMakeLists.txt").read_text()
    for line in expected_content:
        assert line in content
