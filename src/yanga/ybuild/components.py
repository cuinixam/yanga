from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


class BuildComponentType(Enum):
    COMPONENT = auto()
    UNIT = auto()
    CONTAINER = auto()


@dataclass
class BuildComponent:
    #: Component name
    name: str
    #: Component type
    type: BuildComponentType
    #: Is this component a subcomponent of another component
    is_subcomponent: bool = False
    #: Component description
    description: Optional[str] = None
    #: Subcomponents
    components: List["BuildComponent"] = field(default_factory=list)
