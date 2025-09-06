import json
from pathlib import Path
from tempfile import TemporaryDirectory

from yanga.cmake.builder import CMakeBuildSystemGenerator
from yanga.cmake.cmake_backend import CMakeAddExecutable, CMakeCustomTarget, CMakeObjectLibrary
from yanga.cmake.generator import CMakeFile
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.domain.targets import TargetsData


def test_create_target_dependencies_file():
    """Test that create_target_dependencies_file correctly extracts targets from CMake files."""
    with TemporaryDirectory() as temp_dir:
        project_root_dir = Path(temp_dir)
        output_dir = project_root_dir / "output"

        execution_context = ExecutionContext(
            project_root_dir=project_root_dir,
            user_request=UserVariantRequest("test_variant"),
            variant_name="test_variant",
        )

        generator = CMakeBuildSystemGenerator(execution_context, output_dir)

        # Create some mock CMake files with different target types
        cmake_file1 = CMakeFile(Path("test1.cmake"))
        cmake_file1.append(CMakeCustomTarget(name="test_target", description="Test custom target", commands=[], depends=["dependency1", "dependency2"]))
        cmake_file1.append(CMakeAddExecutable(name="test_exe", sources=["main.cpp"], libraries=["lib1", "lib2"]))

        cmake_file2 = CMakeFile(Path("test2.cmake"))
        cmake_file2.append(CMakeObjectLibrary("test_lib", [Path("source1.cpp"), Path("source2.cpp")]))

        cmake_files = [cmake_file1, cmake_file2]

        # Call the method under test
        result_file = generator.create_target_dependencies_file(cmake_files)

        # Parse the generated JSON content
        generated_json = result_file.to_string()
        targets_data = TargetsData.from_dict(json.loads(generated_json))

        # Verify the results
        assert len(targets_data.targets) == 3

        # Check custom target
        custom_target = next(t for t in targets_data.targets if t.name == "test_target")
        assert custom_target.description == "Test custom target"
        assert custom_target.depends == ["dependency1", "dependency2"]

        # Check executable target
        exe_target = next(t for t in targets_data.targets if t.name == "test_exe")
        assert exe_target.description == "Executable target: test_exe"
        assert exe_target.depends == ["lib1", "lib2"]
        assert exe_target.outputs == ["test_exe"]

        # Check object library target
        lib_target = next(t for t in targets_data.targets if t.name == "test_lib_lib")
        assert lib_target.description == "Object library: test_lib"
        assert lib_target.depends == []
        assert lib_target.outputs == ["test_lib_lib"]
