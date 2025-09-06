import sys
from argparse import ArgumentParser
from sys import argv

from py_app_dev.core.cmd_line import CommandLineHandlerBuilder
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, setup_logger

from yanga import __version__
from yanga.commands.cppcheck_report import CppCheckReportCommand
from yanga.commands.filter_compile_commands import FilterCompileCommandsCommand
from yanga.commands.gcovr import CreateComponentGcovrConfigCommand, CreateVariantGcovrConfigCommand, GcovrDocCommand
from yanga.commands.report_config import ReportConfigCommand
from yanga.commands.targets import TargetsDocCommand


def do_run() -> int:
    parser = ArgumentParser(prog="yanga_cmd", description="Yanga CLI utilities", exit_on_error=False)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    builder = CommandLineHandlerBuilder(parser)
    builder.add_commands(
        [
            FilterCompileCommandsCommand(),
            CppCheckReportCommand(),
            ReportConfigCommand(),
            CreateComponentGcovrConfigCommand(),
            CreateVariantGcovrConfigCommand(),
            GcovrDocCommand(),
            TargetsDocCommand(),
        ]
    )
    handler = builder.create()
    return handler.run(argv[1:])


def main() -> int:
    try:
        setup_logger()
        return do_run()
    except UserNotificationException as e:
        logger.error(f"{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
