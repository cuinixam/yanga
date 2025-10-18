from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from yanga.domain.config import DocsConfiguration, TestingConfiguration


@dataclass
class Component:
    #: Component name
    name: str
    #: Component path
    path: Path
    #: Productive sources
    sources: list[str] = field(default_factory=list)
    #: Testing configuration
    testing: Optional[TestingConfiguration] = None
    #: Documentation configuration
    docs: Optional[DocsConfiguration] = None
    #: Include directories paths. The actual paths are to be resolved by the user of this data.
    include_dirs: list[Path] = field(default_factory=list)
    #: Is this component a sub-component of another component
    is_subcomponent: bool = False
    #: Component description
    description: Optional[str] = None
    #: Subcomponents
    components: list["Component"] = field(default_factory=list)
    #: Another name to require this component by alias
    alias: Optional[str] = None

    @property
    def test_sources(self) -> list[str]:
        result = []
        if self.testing and self.testing.sources:
            result.extend(self.testing.sources)
        return result

    @property
    def docs_sources(self) -> list[str]:
        result = []
        if self.docs and self.docs.sources:
            result.extend(self.docs.sources)
        return result
