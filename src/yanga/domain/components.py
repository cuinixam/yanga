from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from yanga.domain.config import TestingConfiguration


@dataclass
class Component:
    #: Component name
    name: str
    #: Component path
    path: Path
    #: Component sources
    sources: list[str] = field(default_factory=list)
    #: Component testing configuration
    testing: Optional[TestingConfiguration] = None
    #: Documentation sources
    docs_sources: list[str] = field(default_factory=list)
    #: Component include directories paths. The actual paths are to be resolved by the user of this data.
    include_dirs: list[Path] = field(default_factory=list)
    #: Is this component a sub-component of another component
    is_subcomponent: bool = False
    #: Component description
    description: Optional[str] = None
    #: Subcomponents
    components: list["Component"] = field(default_factory=list)

    @property
    def test_sources(self) -> list[str]:
        result = []
        if self.testing and self.testing.sources:
            result.extend(self.testing.sources)
        return result
