import json
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from clanguru.doc_generator import MarkdownFormatter

from yanga.cmake.builder import CMakeBuildSystemGenerator
from yanga.cmake.cmake_backend import CMakeAddExecutable, CMakeAddLibrary, CMakeCustomTarget
from yanga.cmake.generator import CMakeFile
from yanga.commands.targets import TargetDependencyTreeBuilder, TargetDocumentationGenerator, TargetsDocCommand
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.domain.targets import Target, TargetsData, TargetType


def test_create_target_dependencies_file():
    with TemporaryDirectory() as temp_dir:
        project_root_dir = Path(temp_dir)
        output_dir = project_root_dir / "output"

        execution_context = ExecutionContext(
            project_root_dir=project_root_dir,
            user_request=UserVariantRequest("test_variant"),
            variant_name="test_variant",
        )

        generator = CMakeBuildSystemGenerator(execution_context, output_dir)

        cmake_file1 = CMakeFile(Path("test1.cmake"))
        cmake_file1.append(CMakeCustomTarget(name="test_target", description="Test custom target", commands=[], depends=["dependency1", "dependency2"]))
        cmake_file1.append(CMakeAddExecutable(name="test_exe", sources=["main.cpp"], libraries=["lib1", "lib2"]))

        cmake_file2 = CMakeFile(Path("test2.cmake"))
        cmake_file2.append(CMakeAddLibrary("test_lib", [Path("source1.cpp"), Path("source2.cpp")]))

        cmake_files = [cmake_file1, cmake_file2]

        result_file = generator.create_target_dependencies_file(cmake_files)

        generated_json = result_file.to_string()
        targets_data = TargetsData.from_dict(json.loads(generated_json))

        assert len(targets_data.targets) == 3

        custom_target = next(t for t in targets_data.targets if t.name == "test_target")
        assert custom_target.description == "Test custom target"
        assert custom_target.depends == ["dependency1", "dependency2"]
        assert custom_target.target_type.to_string() == "CUSTOM_TARGET"

        exe_target = next(t for t in targets_data.targets if t.name == "test_exe")
        assert exe_target.description == "Executable target: test_exe"
        assert exe_target.depends == ["lib1", "lib2"]
        assert exe_target.outputs == ["test_exe"]
        assert exe_target.target_type.to_string() == "EXECUTABLE"

        lib_target = next(t for t in targets_data.targets if t.name == "test_lib_lib")
        assert lib_target.description == "Object library: test_lib"
        assert lib_target.depends == []
        assert lib_target.outputs == ["test_lib_lib"]
        assert lib_target.target_type.to_string() == "OBJECT_LIBRARY"


def test_find_root_targets_custom_targets_only():
    targets_data = TargetsData(
        targets=[
            Target(name="app", description="Main application", depends=["lib1"], outputs=["app.exe"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="lib1", description="Library 1", depends=[], outputs=["lib1.a"], target_type=TargetType.EXECUTABLE),
            Target(name="standalone", description="Standalone", depends=[], outputs=["standalone.exe"], target_type=TargetType.CUSTOM_TARGET),
        ]
    )

    builder = TargetDependencyTreeBuilder(targets_data)
    root_targets = builder.find_root_targets()

    assert len(root_targets) == 2
    root_names = {target.name for target in root_targets}
    assert root_names == {"app", "standalone"}


def test_circular_dependency_handling():
    targets_data = TargetsData(
        targets=[
            Target(name="a", description="Target A", depends=["b"], outputs=["a.exe"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="b", description="Target B", depends=["a"], outputs=["b.a"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="standalone", description="Standalone", depends=[], outputs=["standalone.exe"], target_type=TargetType.CUSTOM_TARGET),
        ]
    )

    builder = TargetDependencyTreeBuilder(targets_data)
    root_targets = builder.find_root_targets()

    assert len(root_targets) == 1
    assert root_targets[0].name == "standalone"

    target_a = next(t for t in targets_data.targets if t.name == "a")
    html = builder.generate_target_tree_html(target_a)
    assert "(circular dependency)" in html


def test_dependency_tree_html_generation():
    targets_data = TargetsData(
        targets=[
            Target(name="app", description="Main app", depends=["lib1", "external_lib"], outputs=["app.exe"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="lib1", description="Library 1", depends=[], outputs=["lib1.a"], target_type=TargetType.EXECUTABLE),
        ]
    )

    builder = TargetDependencyTreeBuilder(targets_data)
    app_target = next(t for t in targets_data.targets if t.name == "app")

    html = builder.generate_target_tree_html(app_target)

    assert "<details>" in html
    assert "<summary><strong>app</strong> - Main app -> [app.exe]</summary>" in html
    assert "<li><strong>lib1</strong> - Library 1 -> [lib1.a]</li>" in html
    assert "<li>external_lib (external dependency)</li>" in html


def test_documentation_generation():
    targets_data = TargetsData(
        targets=[
            Target(name="app", description="Main application", depends=["lib1"], outputs=["app.exe"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="lib1", description="Library 1", depends=[], outputs=["lib1.a"], target_type=TargetType.EXECUTABLE),
            Target(name="test", description="Test executable", depends=[], outputs=["test.exe"], target_type=TargetType.CUSTOM_TARGET),
        ]
    )

    generator = TargetDocumentationGenerator(targets_data)
    doc_structure = generator.create_doc_structure()
    markdown = MarkdownFormatter().format(doc_structure)

    assert "# Target Dependencies Documentation" in markdown
    assert "**Total targets**: 3" in markdown
    assert "**Root targets (CMakeCustomTargets only)**: 2" in markdown
    assert "## Root Targets (CMakeCustomTargets)" in markdown
    assert "### app" in markdown
    assert "### test" in markdown
    assert "## All Targets" not in markdown


def test_empty_targets_handling():
    targets_data = TargetsData(targets=[])
    generator = TargetDocumentationGenerator(targets_data)

    doc_structure = generator.create_doc_structure()
    markdown = MarkdownFormatter().format(doc_structure)

    assert "**Total targets**: 0" in markdown
    assert "**Root targets (CMakeCustomTargets only)**: 0" in markdown


def test_custom_command_grouping():
    """Test that custom commands are grouped by command with their used outputs listed."""
    targets_data = TargetsData(
        targets=[
            Target(
                name="generate_headers",
                target_type=TargetType.CUSTOM_COMMAND,
                description="Generates multiple header files",
                outputs=["config.h", "version.h"],
                depends=[],
            ),
            Target(
                name="module_a",
                target_type=TargetType.CUSTOM_TARGET,
                description="Module A",
                outputs=[],
                depends=["config.h", "version.h"],  # Depends on both outputs from same custom command
            ),
        ]
    )

    tree_builder = TargetDependencyTreeBuilder(targets_data)
    module_a = tree_builder.targets_by_name["module_a"]
    tree_html = tree_builder.generate_target_tree_html(module_a)

    # Should have exactly one custom command entry (grouped)
    custom_command_entries = tree_html.count("<strong>custom command</strong>")
    assert custom_command_entries == 1

    # Should show the used outputs in the grouped entry
    assert "(uses: config.h, version.h)" in tree_html

    # Verify the custom command appears as "custom command" not the actual name
    assert "generate_headers" not in tree_html
    assert "custom command" in tree_html

    # Should not have "see above" since we group instead of duplicate
    see_above_entries = tree_html.count("(see above)")
    assert see_above_entries == 0


def test_complex_custom_command_dependency_chain():
    targets_data = TargetsData(
        targets=[
            # Executable at bottom of chain
            Target(
                name="greeter",
                target_type=TargetType.EXECUTABLE,
                description="Executable target: greeter",
                outputs=["greeter"],
                depends=["external_lib"],
            ),
            # Custom command that depends on executable
            Target(
                name="cmd_run_test",
                target_type=TargetType.CUSTOM_COMMAND,
                description="Run test executable",
                outputs=["test_results.xml"],
                depends=["greeter"],
            ),
            # Custom command that depends on test results
            Target(
                name="cmd_generate_coverage",
                target_type=TargetType.CUSTOM_COMMAND,
                description="Generate coverage report",
                outputs=["coverage.json", "coverage.html"],
                depends=["test_results.xml"],
            ),
            # Custom target that depends on coverage outputs
            Target(
                name="coverage_target",
                target_type=TargetType.CUSTOM_TARGET,
                description="Coverage report target",
                outputs=[],
                depends=["coverage.json", "coverage.html"],
            ),
        ]
    )

    tree_builder = TargetDependencyTreeBuilder(targets_data)
    coverage_target = tree_builder.targets_by_name["coverage_target"]
    tree_html = tree_builder.generate_target_tree_html(coverage_target)

    # Should show the complete dependency chain
    assert "Generate coverage report" in tree_html  # First custom command
    assert "Run test executable" in tree_html  # Second custom command
    assert "Executable target: greeter" in tree_html  # Final executable

    # Should show custom commands as collapsible when they have dependencies
    assert "<details>" in tree_html
    assert "<summary><strong>custom command</strong>" in tree_html

    # Should show external dependencies
    assert "external_lib (external dependency)" in tree_html


@pytest.mark.parametrize(
    "target_type,should_be_root",
    [
        (TargetType.CUSTOM_TARGET, True),
        (TargetType.EXECUTABLE, False),
        (TargetType.OBJECT_LIBRARY, False),
        (TargetType.CUSTOM_COMMAND, False),
    ],
)
def test_root_target_filtering_by_type(target_type: TargetType, should_be_root: bool) -> None:
    targets_data = TargetsData(
        targets=[
            Target(name="target", description="Test target", depends=[], outputs=["output"], target_type=target_type),
        ]
    )

    builder = TargetDependencyTreeBuilder(targets_data)
    root_targets = builder.find_root_targets()

    if should_be_root:
        assert len(root_targets) == 1
        assert root_targets[0].name == "target"
    else:
        assert len(root_targets) == 0


def test_targets_doc_command():
    targets_data = TargetsData(
        targets=[
            Target(name="app", description="Main app", depends=["lib"], outputs=["app.exe"], target_type=TargetType.CUSTOM_TARGET),
            Target(name="lib", description="Library", depends=[], outputs=["lib.a"], target_type=TargetType.EXECUTABLE),
        ]
    )

    with TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / "targets.json"
        targets_data.to_json_file(input_file)

        output_file = Path(temp_dir) / "targets_doc.md"

        command = TargetsDocCommand()
        args = Namespace(variant_targets_data_file=input_file, output_file=output_file)

        result = command.run(args)

        assert result == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "# Target Dependencies Documentation" in content
        assert "app" in content
        assert "CMakeCustomTargets" in content
