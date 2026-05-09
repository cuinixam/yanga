from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from yanga.ymain import app


def test_pristine_flag_is_plumbed_into_run_command_config(tmp_path: Path) -> None:
    with patch("yanga.ymain.RunCommand") as mock_run:
        result = CliRunner().invoke(app, ["run", "--project-dir", str(tmp_path), "--variant", "MyVariant", "--pristine"])

    assert result.exit_code == 0, result.output
    mock_run.return_value.do_run.assert_called_once()
    config = mock_run.return_value.do_run.call_args.args[0]
    assert config.pristine is True
    assert config.variant_name == "MyVariant"


def test_pristine_defaults_to_false_when_flag_omitted(tmp_path: Path) -> None:
    with patch("yanga.ymain.RunCommand") as mock_run:
        result = CliRunner().invoke(app, ["run", "--project-dir", str(tmp_path), "--variant", "MyVariant"])

    assert result.exit_code == 0, result.output
    config = mock_run.return_value.do_run.call_args.args[0]
    assert config.pristine is False
