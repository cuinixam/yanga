from abc import ABC, abstractmethod
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict, List

from yanga.core.docs_utils import fulfills
from yanga.core.logger import logger


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

    def __init__(self) -> None:
        self.commands: Dict[str, Command] = {}
        self.parser = ArgumentParser(
            prog="yanga", description="Yanga CLI", exit_on_error=False
        )
        self.subparsers = self.parser.add_subparsers(title="Commands", dest="command")

    def create(self) -> CommandLineHandler:
        return CommandLineHandler(self.commands, self.parser)

    @fulfills("REQ-CMDLINE_REGISTER_COMMANDS-0.0.1", "REQ-CMDLINE_DUPLICATION-0.0.1")
    def add_command(self, command: Command) -> "CommandLineHandlerBuilder":
        """Add a command to the command line handler."""
        if self.commands.get(command.name, None) is not None:
            raise ValueError(f"Command {command.name} already exists")
        self.commands[command.name] = command
        command.register_parser(self.subparsers)
        return self
