from pathlib import Path
from typing import Any, List

from .artifacts import ProjectArtifactsLocator
from .components import Component


def make_list_unique(seq: List[Any]) -> List[Any]:
    # dict.fromkeys keeps the order of the list and removes duplicates
    return list(dict.fromkeys(seq))


class ComponentAnalyzer:
    def __init__(self, components: List[Component], artifacts_locator: ProjectArtifactsLocator) -> None:
        self.components = components
        self.artifacts_locator = artifacts_locator

    def collect_sources(self) -> List[Path]:
        files: List[Path] = []
        for component in self.components:
            files.extend([self.locate_component_file(component, source) for source in component.sources])
        return files

    def collect_test_sources(self) -> List[Path]:
        files: List[Path] = []
        for component in self.components:
            files.extend([self.locate_component_file(component, source) for source in component.test_sources])
        return files

    def collect_include_directories(self) -> List[Path]:
        # TODO: check if there are specific include directories for each component
        includes = [path.parent for path in self.collect_sources()]
        # remove duplicates and return
        return make_list_unique(includes)

    def get_testable_components(self) -> List[Component]:
        return [component for component in self.components if component.test_sources]

    def is_testable(self) -> bool:
        return any(component.test_sources for component in self.components)

    def locate_component_file(self, component: Component, file: str) -> Path:
        return self.artifacts_locator.locate_artifact(file, [component.path])
