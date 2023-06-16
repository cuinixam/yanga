import json
import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("build")


class Build:
    pass


def main() -> int:
    logger.debug("".join(["-" for _ in range(80)]))
    logger.debug("Environment: \n" + json.dumps(dict(os.environ), indent=4))
    logger.info("".join(["-" for _ in range(80)]))
    logger.info(f"Arguments: {sys.argv[1:]}")
    logger.info("".join(["-" for _ in range(80)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
