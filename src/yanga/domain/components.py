from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Component:
    #: Component name
    name: str
    #: Component path
    path: Path
    #: Component sources
    sources: list[str] = field(default_factory=list)
    #: Component test sources
    test_sources: list[str] = field(default_factory=list)
    #: Component include directories paths. The actual paths are to be resolved by the user of this data.
    include_dirs: list[Path] = field(default_factory=list)
    #: Is this component a sub-component of another component
    is_subcomponent: bool = False
    #: Component description
    description: Optional[str] = None
    #: Subcomponents
    components: list["Component"] = field(default_factory=list)
