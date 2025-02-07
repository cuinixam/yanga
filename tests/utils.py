from pathlib import Path
from typing import Callable, List, Optional, Type, TypeVar

from yanga.cmake.cmake_backend import CMakeElement

T = TypeVar("T", bound=CMakeElement)


class CMakeAnalyzer:
    def __init__(self, elements: List[CMakeElement]):
        self.elements = elements

    def find_elements_of_type(self, element_type: Type[T]) -> List[T]:
        """Find all elements of a specific type."""
        return [elem for elem in self.elements if isinstance(elem, element_type)]

    def _assert_elements(self, element_type: Type[T], expected_count: int, filter_fn: Optional[Callable[[T], bool]] = None) -> List[T]:
        """Helper method to assert and return elements based on type and optional filter."""
        elements = self.find_elements_of_type(element_type)

        assert elements, f"No element of type {element_type.__name__} found"

        filtered_elements = elements
        if filter_fn:
            filtered_elements = [elem for elem in elements if filter_fn(elem)]
            assert filtered_elements, f"Found {len(elements)} elements of type {element_type.__name__}, but none met the filter criteria"

        assert len(filtered_elements) == expected_count, (
            f"Expected {expected_count} elements of type {element_type.__name__} that met the criteria, but found {len(filtered_elements)}"
        )

        return filtered_elements

    def assert_element_of_type(self, element_type: Type[T], filter_fn: Optional[Callable[[T], bool]] = None) -> T:
        """Assert that exactly one element of the given type exists, optionally needs to meet filter condition."""
        return self._assert_elements(element_type, 1, filter_fn)[0]

    def assert_elements_of_type(self, element_type: Type[T], count: int, filter_fn: Optional[Callable[[T], bool]] = None) -> List[T]:
        """Assert that exactly `count` elements of the given type exist, optionally needs to meet filter condition."""
        return self._assert_elements(element_type, count, filter_fn)


def write_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file


def this_repository_root_dir() -> Path:
    return Path(__file__).parent.parent.absolute()
