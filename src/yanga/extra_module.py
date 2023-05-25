from loguru import logger


class ExtraModule:
    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = logger.bind()

    def run(self) -> None:
        self.logger.info("Running extra module")
