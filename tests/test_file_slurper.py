import pytest

from yanga.domain.config_slurper import find_files


# Fixture to create a temporary directory structure for testing
@pytest.fixture
def test_directory(tmp_path):
    # Define directory structure
    dirs = {
        "dir1": ["file1.yaml", "file1.txt"],
        "dir2": ["file2.yaml"],
        "dir2/skip_this_dir": ["file3.yaml"],
    }

    # Create directories and files
    for dirpath, filenames in dirs.items():
        current_dir = tmp_path / dirpath
        current_dir.mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            file_path = current_dir / filename
            file_path.touch()

    return tmp_path


def test_finding_files_without_exclusions(test_directory):
    """Test that find_files function finds all .yaml files without any exclusions."""
    found_files = find_files(test_directory, "*.yaml")
    assert len(found_files) == 3


def test_finding_files_with_exclusions(test_directory):
    """Test that find_files function correctly excludes specified directories."""
    exclude_dirs = ["dir2/skip_this_dir"]
    found_files = find_files(test_directory, "*.yaml", exclude_dirs=exclude_dirs)
    assert len(found_files) == 2
    assert test_directory / "dir2" / "skip_this_dir" / "file3.yaml" not in found_files


def test_finding_files_with_nonexistent_exclusions(test_directory):
    """Test that specifying a nonexistent directory in exclusions doesn't affect results."""
    exclude_dirs = ["nonexistent_dir"]
    found_files = find_files(test_directory, "*.yaml", exclude_dirs=exclude_dirs)
    assert len(found_files) == 3


def test_no_files_found(test_directory):
    """Test that find_files function returns an empty set if no files match the pattern."""
    found_files = find_files(test_directory, "*.nonexistent")
    assert len(found_files) == 0
