from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from mashumaro import DataClassDictMixin
from pick import pick
from py_app_dev.core.logging import logger

T = TypeVar("T", bound=DataClassDictMixin)


class CommandConfigFactory:
    @staticmethod
    def create_config(config_class: Type[T], namespace: Namespace) -> T:
        """
        Creates a configuration instance from an argparse Namespace for the given class.

        Parameters:
        - cls: The class type to instantiate, inheriting from DataClassDictMixin.
        - namespace: The argparse Namespace containing configuration data.

        Returns:
        An instance of cls populated with data from namespace.
        """
        return config_class.from_dict(vars(namespace))


@dataclass
class CommandConfigBase(DataClassDictMixin):
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={"help": "Project root directory. Defaults to the current directory if not specified."},
    )


def prompt_user_to_select_option(options: List[str]) -> Optional[str]:
    if not options:
        return None
    try:
        # TODO: this message is only necessary in case the user will press Ctrl+C to quit.
        # In this case, after pick method returns, the execution is paused until the user presses any key.
        # I have no idea why that happens.
        logger.info("Press any key to continue...")
        selected_variant, _ = pick(options, "Select a variant: ", indicator="=>")
    except KeyboardInterrupt:
        selected_variant = None
    return str(selected_variant) if selected_variant else None
