import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger

ylogger = logger

# Adding custom logging levels
ylogger.level("START", no=38, color="<yellow>")
ylogger.level("STOP", no=39, color="<yellow>")


def time_it(message: Optional[str] = None) -> Callable[..., Any]:
    def _time_it(func: Callable[..., Any]) -> Callable[..., Any]:
        text = message or f"{func.__module__}.{func.__qualname__}"

        def time_it(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            ylogger.log("START", f"Starting {text}")
            result = func(*args, **kwargs)
            end_time = time.time()
            ylogger.log("STOP", f"Finished {text} in {end_time-start_time:.2f}s")
            return result

        return time_it

    return _time_it


def setup_logger(log_file: Optional[Path] = None, clear: bool = True) -> None:
    """Setup logger to stdout and optionally to file."""
    ylogger.remove()
    ylogger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | <level>{message}</level>",
    )
    if log_file is not None:
        ylogger.add(log_file, level="DEBUG")
        # Clear log file
        if log_file.exists() and clear:
            log_file.write_text("")
