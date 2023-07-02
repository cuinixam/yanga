from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pytest

from yanga.core.cmd_line import (
    Command,
    CommandLineHandlerBuilder,
    register_arguments_for_config_dataclass,
)
from yanga.core.docs_utils import validates


class MockCommand(Command):
    def __init__(self, name: str, description: str, arguments: List[str]) -> None:
        super().__init__(name, description)
        self.arguments = arguments
        self.called_with_args = Namespace()

    def run(self, args: Namespace) -> int:
        print(f"Running {self.name} with args {args}")
        self.called_with_args = args
        return 0

    def _register_arguments(self, parser):
        for arg in self.arguments:
            parser.add_argument(arg, help=f"Some description for {arg}.")


@validates(
    "REQ-CMDLINE_REGISTER_COMMANDS-0.0.1",
    "REQ-CMDLINE_COMMAND_ARGS-0.0.1",
    "REQ-CMDLINE_COMMAND_EXEC-0.0.1",
)
def test_register_commands():
    builder = CommandLineHandlerBuilder()
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    cmd2 = MockCommand("cmd2", "Command 2", ["--arg3", "--arg4"])
    builder.add_command(cmd2)
    handler = builder.create()
    assert set(handler.commands) == {"cmd1", "cmd2"}
    handler.run(["cmd1", "--arg1", "value1", "--arg2", "value2"])
    assert vars(cmd1.called_with_args) == {
        "arg1": "value1",
        "arg2": "value2",
        "command": "cmd1",
    }


@validates("REQ-CMDLINE_UNKNOWN_COMMAND-0.0.1")
def test_unknown_commands():
    builder = CommandLineHandlerBuilder()
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    handler = builder.create()
    assert handler.run(["cmdX", "--arg1", "value1"]) == 1


@validates("REQ-CMDLINE_DUPLICATION-0.0.1")
def test_duplicate_commands():
    builder = CommandLineHandlerBuilder()
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    with pytest.raises(ValueError):
        builder.add_command(cmd1)


@dataclass
class MyConfigDataclass:
    my_first_arg: Path = field(metadata={"help": "Some help for arg1."})
    arg: str = field(default="value1", metadata={"help": "Some help for arg1."})


def test_register_arguments_for_config_dataclass():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, MyConfigDataclass)
    args = parser.parse_args(["--my-first-arg", "my/path", "--arg", "value2"])
    assert vars(args) == {"my_first_arg": Path("my/path"), "arg": "value2"}
