from yanga.core.docs_utils import validates
from yanga.core.logging import logger, setup_logger, time_it


@validates("REQ-LOGGING_FILE-0.0.1")
def test_setup_logger(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logger(log_file, clear=True)
    logger.debug("Test")
    assert log_file.exists()


@time_it("My cool function")
def _some_func() -> None:
    logger.debug("I am some_func")


@validates("REQ-LOGGING_TIME_IT-0.0.1")
def test_time_it(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logger(log_file, clear=True)
    _some_func()
    log_text = log_file.read_text()
    assert "Starting My cool function" in log_text
    assert "I am some_func" in log_text
