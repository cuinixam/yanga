import sys
from argparse import ArgumentParser
from sys import argv

from yanga import __version__
from yanga.commands.build import BuildCommand
from yanga.commands.init import InitCommand
from yanga.commands.install import InstallCommand
from yanga.core.cmd_line import CommandLineHandlerBuilder
from yanga.core.exceptions import UserNotificationException
from yanga.core.logging import logger, setup_logger


def do_run() -> None:
    parser = ArgumentParser(prog="yanga", description="Yanga CLI", exit_on_error=False)
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    builder = CommandLineHandlerBuilder(parser)
    builder.add_commands([BuildCommand(), InitCommand(), InstallCommand()])
    handler = builder.create()
    handler.run(argv[1:])


def main() -> int:
    try:
        setup_logger()
        do_run()
    except UserNotificationException as e:
        logger.error(f"{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
