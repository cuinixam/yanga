from pathlib import Path

import pytest

from yanga.zephyr.kconfig_frontend import merge_into


@pytest.mark.parametrize(
    ("existing", "changed", "expected"),
    [
        ("", {"LOG": "CONFIG_LOG=y\n"}, "CONFIG_LOG=y\n"),
        ("CONFIG_LOG=n\nCONFIG_GPIO=y\n", {"LOG": "CONFIG_LOG=y\n"}, "CONFIG_LOG=y\nCONFIG_GPIO=y\n"),
        ("# CONFIG_LOG is not set\n", {"LOG": "CONFIG_LOG=y\n", "SHELL": "CONFIG_SHELL=y\n"}, "CONFIG_LOG=y\nCONFIG_SHELL=y\n"),
    ],
)
def test_merge_into_keeps_untouched_lines_in_place(tmp_path: Path, existing: str, changed: dict[str, str], expected: str) -> None:
    selection = tmp_path / "config.txt"
    if existing:
        selection.write_text(existing)

    assert merge_into(selection, "CONFIG_", changed) == expected
