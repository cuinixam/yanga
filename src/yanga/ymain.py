import sys
from pathlib import Path
from sys import argv

from yanga.commands.build import BuildCommand
from yanga.commands.init import InitCommand
from yanga.core.cmd_line import CommandLineHandlerBuilder
from yanga.core.exceptions import UserNotificationException
from yanga.core.logger import logger, setup_logger, time_it


@time_it()
def do_run() -> None:
    logger.debug("Starting yanga")
    builder = CommandLineHandlerBuilder()
    builder.add_command(BuildCommand()).add_command(InitCommand())
    handler = builder.create()
    handler.run(argv[1:])


def main() -> int:
    try:
        setup_logger(Path(".yanga/logs/yanga.log"), clear=True)
        do_run()
    except UserNotificationException as e:
        logger.error(f"{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
