from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from yanga.cmake.cmake_backend import CMakeElement

T = TypeVar("T", bound=CMakeElement)
U = TypeVar("U")


def find_elements_of_type(elements: list[Any], element_type: type[T]) -> list[T]:
    """Find all elements of a specific type."""
    return [elem for elem in elements if isinstance(elem, element_type)]


def find_elements_of_any_type(elements: list[Any], element_type: type[U]) -> list[U]:
    """Find all elements of a specific type (generic version)."""
    return [elem for elem in elements if isinstance(elem, element_type)]


def _assert_elements(elements: list[Any], element_type: type[T], expected_count: int, filter_fn: Optional[Callable[[T], bool]] = None) -> list[T]:
    """Helper method to assert and return elements based on type and optional filter."""
    elements = find_elements_of_type(elements, element_type)

    if expected_count != 0:
        assert elements, f"No element of type {element_type.__name__} found"

    filtered_elements = elements
    if filter_fn:
        filtered_elements = [elem for elem in elements if filter_fn(elem)]

    assert len(filtered_elements) == expected_count, f"Expected {expected_count} elements of type {element_type.__name__} that met the criteria, but found {len(filtered_elements)}"

    return filtered_elements


def _assert_elements_generic(elements: list[Any], element_type: type[U], expected_count: int, filter_fn: Optional[Callable[[U], bool]] = None) -> list[U]:
    """Helper method to assert and return elements based on type and optional filter (generic version)."""
    found_elements = find_elements_of_any_type(elements, element_type)

    if expected_count != 0:
        assert found_elements, f"No element of type {element_type.__name__} found"

    filtered_elements = found_elements
    if filter_fn:
        filtered_elements = [elem for elem in found_elements if filter_fn(elem)]

    assert len(filtered_elements) == expected_count, f"Expected {expected_count} elements of type {element_type.__name__} that met the criteria, but found {len(filtered_elements)}"

    return filtered_elements


def assert_element_of_type(elements: list[Any], element_type: type[T], filter_fn: Optional[Callable[[T], bool]] = None) -> T:
    """Assert that exactly one element of the given type exists, optionally needs to meet filter condition."""
    return _assert_elements(elements, element_type, 1, filter_fn)[0]


def assert_element_of_any_type(elements: list[Any], element_type: type[U], filter_fn: Optional[Callable[[U], bool]] = None) -> U:
    """Assert that exactly one element of the given type exists, optionally needs to meet filter condition (generic version)."""
    return _assert_elements_generic(elements, element_type, 1, filter_fn)[0]


def assert_elements_of_type(elements: list[Any], element_type: type[T], count: int, filter_fn: Optional[Callable[[T], bool]] = None) -> list[T]:
    """Assert that exactly `count` elements of the given type exist, optionally needs to meet filter condition."""
    return _assert_elements(elements, element_type, count, filter_fn)


def assert_elements_of_any_type(elements: list[Any], element_type: type[U], count: int, filter_fn: Optional[Callable[[U], bool]] = None) -> list[U]:
    """Assert that exactly `count` elements of the given type exist, optionally needs to meet filter condition (generic version)."""
    return _assert_elements_generic(elements, element_type, count, filter_fn)


def write_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file


def this_repository_root_dir() -> Path:
    return Path(__file__).parent.parent.absolute()
