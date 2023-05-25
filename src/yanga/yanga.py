import time
from pathlib import Path

from yanga.extra_module import ExtraModule
from yanga.ylog import setup_logger, time_it, ylogger


class Yanga:
    def __init__(self) -> None:
        self.logger = ylogger.bind()

    @time_it()
    def run(self) -> None:
        self.logger.info("Yanga is running")
        time.sleep(0.3)
        ExtraModule("extra cool").run()


@time_it()
def do_run() -> None:
    ylogger.debug("Starting yanga")
    yanga = Yanga()
    yanga.run()


def main() -> None:
    setup_logger(Path("logs/yanga.log"), clear=True)
    do_run()


if __name__ == "__main__":
    main()
