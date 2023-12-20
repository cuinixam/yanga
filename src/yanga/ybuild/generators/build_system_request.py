from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BuildSystemCommand(Enum):
    NONE = "none"
    ALL = "all"
    CUSTOM = "custom"
    CLEAN = "clean"
    BUILD = "build"
    TEST = "test"
    COMPILE = "compile"


@dataclass
class BuildSystemRequest:
    variant_name: str
    component_name: Optional[str] = None
    command: BuildSystemCommand = BuildSystemCommand.ALL

    @property
    def target_name(self) -> str:
        if self.component_name:
            return f"{self.component_name}_{self.command.value}"
        return self.command.value if self.command else "all"


class CustomBuildSystemRequest(BuildSystemRequest):
    def __init__(self, variant_name: str, custom_request: str) -> None:
        super().__init__(variant_name, None, BuildSystemCommand.CUSTOM)
        self.custom_request = custom_request

    @property
    def target_name(self) -> str:
        return self.custom_request


class BuildVariantRequest(BuildSystemRequest):
    def __init__(self, variant_name: str) -> None:
        super().__init__(variant_name, None, BuildSystemCommand.BUILD)


class TestVariantRequest(BuildSystemRequest):
    def __init__(self, variant_name: str) -> None:
        super().__init__(variant_name, None, BuildSystemCommand.TEST)


class CleanVariantRequest(BuildSystemRequest):
    def __init__(self, variant_name: str) -> None:
        super().__init__(variant_name, None, BuildSystemCommand.CLEAN)


class CompileComponentRequest(BuildSystemRequest):
    def __init__(self, variant_name: str, component_name: str) -> None:
        super().__init__(variant_name, component_name, BuildSystemCommand.COMPILE)


class TestComponentRequest(BuildSystemRequest):
    def __init__(self, variant_name: str, component_name: str) -> None:
        super().__init__(variant_name, component_name, BuildSystemCommand.TEST)
