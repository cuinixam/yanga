from pathlib import Path
from sys import argv

from yanga.core.cmd_line import CommandLineHandlerBuilder
from yanga.core.logger import logger, setup_logger, time_it
from yanga.ybuild import BuildCommand
from yanga.yinit import InitCommand


@time_it()
def do_run() -> None:
    logger.debug("Starting yanga")
    builder = CommandLineHandlerBuilder()
    builder.add_command(BuildCommand()).add_command(InitCommand())
    handler = builder.create()
    handler.run(argv[1:])


def main() -> None:
    setup_logger(Path(".yanga/logs/yanga.log"), clear=True)
    do_run()


if __name__ == "__main__":
    main()
