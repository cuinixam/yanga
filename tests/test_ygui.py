from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from py_app_dev.mvp.event_manager import EventManager
from yanga_core.commands.run import RunCommandConfig

from yanga.gui.ygui import YangaEvent, YangaPresenter


@pytest.fixture
def presenter(tmp_path: Path) -> YangaPresenter:
    """Build a presenter with a Mock view so we don't construct any tk widgets."""
    view = Mock()
    with patch.object(YangaPresenter, "_load_project_state"):
        return YangaPresenter(view, EventManager(), tmp_path)


class _SyncThread:
    """Stand-in for ``threading.Thread`` that runs the target on ``start()`` synchronously."""

    def __init__(self, *_args: object, target: object, **_kwargs: object) -> None:
        self._target = target

    def start(self) -> None:
        self._target()  # type: ignore[operator]


def _captured_config(presenter: YangaPresenter, event: YangaEvent, *args: object) -> RunCommandConfig:
    fire = presenter.event_manager.create_event_trigger(event)
    with patch("yanga.gui.ygui.threading.Thread", _SyncThread), patch("yanga.gui.ygui.RunCommand") as mock_run:
        fire(*args)
    mock_run.return_value.do_run.assert_called_once()
    config = mock_run.return_value.do_run.call_args.args[0]
    assert isinstance(config, RunCommandConfig)
    return config


def test_component_clean_event_dispatches_run_with_clean_target(presenter: YangaPresenter) -> None:
    presenter.selected_variant = "MyVariant"
    presenter.selected_platform = "host"
    config = _captured_config(presenter, YangaEvent.COMPONENT_CLEAN_EVENT, "MyVariant", "CompA", "Debug")
    assert config.variant_name == "MyVariant"
    assert config.component_name == "CompA"
    assert config.target == "clean"
    assert config.build_type == "Debug"
    assert config.platform == "host"
    assert config.not_interactive is True
    assert config.pristine is False


def test_build_event_with_pristine_flag_propagates_to_run_config(presenter: YangaPresenter) -> None:
    presenter.selected_variant = "MyVariant"
    presenter.selected_platform = "host"
    config = _captured_config(presenter, YangaEvent.BUILD_EVENT, "MyVariant", "Debug", None, True)
    assert config.target == "build"
    assert config.pristine is True
    assert config.component_name is None


def test_build_event_without_pristine_flag_defaults_to_false(presenter: YangaPresenter) -> None:
    presenter.selected_variant = "MyVariant"
    presenter.selected_platform = "host"
    config = _captured_config(presenter, YangaEvent.BUILD_EVENT, "MyVariant", "Debug", None, False)
    assert config.pristine is False


def test_component_build_event_propagates_pristine(presenter: YangaPresenter) -> None:
    presenter.selected_variant = "MyVariant"
    presenter.selected_platform = "host"
    config = _captured_config(presenter, YangaEvent.COMPONENT_BUILD_EVENT, "MyVariant", "CompA", "Debug", None, True)
    assert config.target == "build"
    assert config.component_name == "CompA"
    assert config.pristine is True


def test_clean_variant_event_does_not_set_pristine(presenter: YangaPresenter) -> None:
    presenter.selected_variant = "MyVariant"
    presenter.selected_platform = "host"
    config = _captured_config(presenter, YangaEvent.CLEAN_VARIANT_EVENT, "MyVariant")
    assert config.target == "clean"
    assert config.component_name is None
    assert config.pristine is False
