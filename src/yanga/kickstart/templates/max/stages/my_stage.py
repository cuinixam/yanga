from pathlib import Path

from py_app_dev.core.logging import logger

from yanga.ybuild.pipeline import Stage


class MyStage(Stage):
    def run(self) -> int:
        logger.info(f"Running my stage with output dir '{self.output_dir}'")
        return 0

    def get_name(self) -> str:
        return "my_stage"

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []
