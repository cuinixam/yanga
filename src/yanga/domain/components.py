from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class ComponentType(Enum):
    COMPONENT = auto()
    UNIT = auto()
    CONTAINER = auto()


@dataclass
class Component:
    #: Component name
    name: str
    #: Component type
    type: ComponentType
    #: Component path
    path: Path
    #: Component sources
    sources: list[str] = field(default_factory=list)
    #: Component test sources
    test_sources: list[str] = field(default_factory=list)
    #: Component include directories
    include_dirs: list[str] = field(default_factory=list)
    #: Is this component a sub-component of another component
    is_subcomponent: bool = False
    #: Component description
    description: Optional[str] = None
    #: Subcomponents
    components: list["Component"] = field(default_factory=list)
