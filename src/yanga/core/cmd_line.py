import dataclasses
from abc import ABC, abstractmethod
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict, List, Type

from .docs_utils import fulfills
from .logging import logger


class Command(ABC):
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.parser: ArgumentParser

    @abstractmethod
    def run(self, args: Namespace) -> int:
        """Run the command with the provided arguments."""

    def register_parser(self, parser_adder) -> None:  # type: ignore
        """Register the command parser.

        :param parser_adder: The return value of ``ArgumentParser.add_subparsers()``
        """
        self.parser = parser_adder.add_parser(
            self.name, help=self.description, exit_on_error=False
        )
        self._register_arguments(self.parser)

    @abstractmethod
    def _register_arguments(self, parser: ArgumentParser) -> None:
        """Register arguments for the command."""


class CommandLineHandler:
    """Handles the command line interface."""

    def __init__(self, commands: Dict[str, Command], parser: ArgumentParser) -> None:
        super().__init__()
        self.commands = commands
        self.parser = parser
        self.logger = logger.bind()

    @fulfills("REQ-CMDLINE_COMMAND_ARGS-0.0.1", "REQ-CMDLINE_COMMAND_EXEC-0.0.1")
    def run(self, args: List[str]) -> int:
        try:
            parsed_args = self.parser.parse_args(args)
        except ArgumentError as e:
            self.logger.error(f"Argument error: {e}")
            self.parser.print_help()
            return 1
        if (args is None) or (len(args) == 0):
            self.logger.debug("No command provided")
            self.parser.print_help()
            return 1
        command = self.commands.get(args[0], None)
        if command:
            return command.run(parsed_args)
        else:
            self.logger.error(f"Command {args[0]} not registered")
            return 1


class CommandLineHandlerBuilder:
    """Builds a command line handler."""

    def __init__(self, parser: ArgumentParser) -> None:
        self.commands: Dict[str, Command] = {}
        self.parser = parser
        self.subparsers = self.parser.add_subparsers(title="Commands", dest="command")

    def create(self) -> CommandLineHandler:
        return CommandLineHandler(self.commands, self.parser)

    def add_commands(self, commands: List[Command]) -> "CommandLineHandlerBuilder":
        for command in commands:
            self.add_command(command)
        return self

    @fulfills("REQ-CMDLINE_REGISTER_COMMANDS-0.0.1", "REQ-CMDLINE_DUPLICATION-0.0.1")
    def add_command(self, command: Command) -> "CommandLineHandlerBuilder":
        """Add a command to the command line handler."""
        if self.commands.get(command.name, None) is not None:
            raise ValueError(f"Command {command.name} already exists")
        self.commands[command.name] = command
        command.register_parser(self.subparsers)
        return self


def register_arguments_for_config_dataclass(
    parser: ArgumentParser, config_dataclass: Type  # type: ignore
) -> None:
    """Helper function to register arguments for a dataclass.
    This avoid having to manually register arguments for each field of the dataclass."""
    if not dataclasses.is_dataclass(config_dataclass):
        raise TypeError(f"{config_dataclass.__name__} is not a dataclass.")

    for field_name, field in config_dataclass.__dataclass_fields__.items():
        parameter_default = (
            field.default if not field.default == dataclasses.MISSING else None
        )
        parameter_help = field.metadata.get(
            "help", f"Value for {field_name}. Default: {parameter_default}"
        )
        parameter_name = field_name.replace("_", "-")

        # TODO: this should be false if the type is Optional
        parameter_required = False if parameter_default else True

        parser.add_argument(
            f"--{parameter_name}",
            required=parameter_required,
            type=field.type,
            default=parameter_default,
            help=parameter_help,
        )
