import io
import json
import traceback
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import auto
from pathlib import Path

from py_app_dev.core.exceptions import UserNotificationException

from yanga.domain.config import BaseConfigJSONMixin, StringableEnum, stringable_enum_field_metadata


class TargetType(StringableEnum):
    """Types of CMake targets for better categorization and filtering."""

    CUSTOM_TARGET = auto()
    CUSTOM_COMMAND = auto()
    EXECUTABLE = auto()
    OBJECT_LIBRARY = auto()


@dataclass
class Target(BaseConfigJSONMixin):
    """Build environment target that can be executed."""

    name: str
    description: str | None = None
    depends: Sequence[str | Path] = field(default_factory=list)
    outputs: Sequence[str | Path] = field(default_factory=list)
    target_type: TargetType = field(default=TargetType.CUSTOM_TARGET, metadata=stringable_enum_field_metadata(TargetType))


@dataclass
class TargetsData(BaseConfigJSONMixin):
    targets: Sequence[Target] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, file_path: Path) -> "TargetsData":
        try:
            result = cls.from_dict(json.loads(file_path.read_text()))
        except Exception as e:
            output = io.StringIO()
            traceback.print_exc(file=output)
            raise UserNotificationException(output.getvalue()) from e
        return result
