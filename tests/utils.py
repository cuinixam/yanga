from pathlib import Path
from typing import List, Type, TypeVar

from yanga.cmake.cmake_backend import CMakeElement

T = TypeVar("T", bound=CMakeElement)


class CMakeAnalyzer:
    def __init__(self, elements: List[CMakeElement]):
        self.elements = elements

    def find_elements_of_type(self, element_type: Type[T]) -> List[T]:
        return [elem for elem in self.elements if isinstance(elem, element_type)]

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


def write_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file
