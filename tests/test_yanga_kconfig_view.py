import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.yview import YangaKConfigData, edit_variant_features


def _write_kconfig_project(tmp_path: Path) -> None:
    """Create a minimal KConfig project with two variants for the edit tests."""
    (tmp_path / "KConfig").write_text(
        textwrap.dedent(
            """\
            config LANG_DE
                bool "German language"
                default n
            """
        )
    )
    (tmp_path / "config_de.txt").write_text("CONFIG_LANG_DE=y\n")
    (tmp_path / "yanga.yaml").write_text(
        textwrap.dedent(
            """\
            variants:
              - name: EnglishVariant
                components:
                - main
              - name: GermanVariant
                components:
                - main
                features_selection_file: "config_de.txt"
            """
        )
    )


def test_yanga_kconfig_data_no_kconfig_file(tmp_path: Path) -> None:
    """Test YangaKConfigData raises exception when KConfig file is missing."""
    with pytest.raises(UserNotificationException, match="KConfig file not found"):
        YangaKConfigData(tmp_path)


def test_yanga_kconfig_data_with_variants(tmp_path: Path) -> None:
    """Test YangaKConfigData loads variants with feature configurations."""
    # Create KConfig file
    kconfig_file = tmp_path / "KConfig"
    kconfig_file.write_text(
        textwrap.dedent(
            """\
            config LANG_DE
                bool "German language"
                default n

            config DEBUG_MODE
                bool "Enable debug mode"
                default y
            """
        )
    )

    # Create variant config file
    config_de_file = tmp_path / "config_de.txt"
    config_de_file.write_text("CONFIG_LANG_DE=y\nCONFIG_DEBUG_MODE=n\n")

    # Create yanga.yaml with variants
    yanga_config = tmp_path / "yanga.yaml"
    yanga_config.write_text(
        textwrap.dedent(
            """\
            variants:
              - name: EnglishVariant
                description: Say hello in English.
                components:
                - main
              - name: GermanVariant
                description: Say hello in German.
                components:
                - main
                features_selection_file: "config_de.txt"
            """
        )
    )

    # Test the YangaKConfigData
    kconfig_data = YangaKConfigData(tmp_path)

    # Test get_elements
    elements = kconfig_data.get_elements()
    assert len(elements) == 2
    element_names = [elem.name for elem in elements]
    assert "LANG_DE" in element_names
    assert "DEBUG_MODE" in element_names

    # Test get_variants
    variants = kconfig_data.get_variants()
    assert len(variants) == 2

    # Find variants by name
    english_variant = next((v for v in variants if v.name == "EnglishVariant"), None)
    german_variant = next((v for v in variants if v.name == "GermanVariant"), None)

    assert english_variant is not None
    assert german_variant is not None

    # Test variant configurations
    # English variant should have default values (LANG_DE=n, DEBUG_MODE=y)
    assert english_variant.config_dict.get("LANG_DE") is not None
    assert english_variant.config_dict.get("DEBUG_MODE") is not None

    # German variant should have overridden values (LANG_DE=y, DEBUG_MODE=n)
    assert german_variant.config_dict.get("LANG_DE") is not None
    assert german_variant.config_dict.get("DEBUG_MODE") is not None

    # Test find_variant_config
    german_config = kconfig_data.find_variant_config("GermanVariant")
    assert german_config is not None
    assert german_config.name == "GermanVariant"

    # Test refresh_data doesn't crash
    kconfig_data.refresh_data()


def test_yanga_kconfig_data_no_variants(tmp_path: Path) -> None:
    """Test YangaKConfigData creates default variant when no variants defined."""
    # Create KConfig file
    kconfig_file = tmp_path / "KConfig"
    kconfig_file.write_text(
        textwrap.dedent(
            """\
            config TEST_FEATURE
                bool "Test feature"
                default y
            """
        )
    )

    # Create empty yanga.yaml (no variants)
    yanga_config = tmp_path / "yanga.yaml"
    yanga_config.write_text("components: []\n")

    # Test the YangaKConfigData
    kconfig_data = YangaKConfigData(tmp_path)

    # Should create a default variant
    variants = kconfig_data.get_variants()
    assert len(variants) == 1
    assert variants[0].name == "Default"

    # Should have the test feature
    elements = kconfig_data.get_elements()
    assert len(elements) == 1
    assert elements[0].name == "TEST_FEATURE"


def test_edit_variant_features_opens_editor_for_named_variant(tmp_path: Path) -> None:
    """A named variant opens its editor directly, defaulting to the GUI editor."""
    _write_kconfig_project(tmp_path)
    with patch("kspl.kconfig.KConfig.menu_config") as menu_config:
        edit_variant_features(tmp_path, "GermanVariant", gui=True)
    menu_config.assert_called_once_with(gui=True)


def test_edit_variant_features_no_gui_uses_menuconfig(tmp_path: Path) -> None:
    """--no-gui forwards gui=False to the editor (terminal menuconfig)."""
    _write_kconfig_project(tmp_path)
    with patch("kspl.kconfig.KConfig.menu_config") as menu_config:
        edit_variant_features(tmp_path, "GermanVariant", gui=False)
    menu_config.assert_called_once_with(gui=False)


def test_edit_variant_features_prompts_when_no_variant(tmp_path: Path) -> None:
    """When no variant is given, the user is prompted to select one."""
    _write_kconfig_project(tmp_path)
    with (
        patch("yanga.yview.prompt_user_to_select_option", return_value="GermanVariant") as prompt,
        patch("kspl.kconfig.KConfig.menu_config") as menu_config,
    ):
        edit_variant_features(tmp_path, None, gui=True)
    prompt.assert_called_once()
    menu_config.assert_called_once_with(gui=True)


def test_edit_variant_features_unknown_variant_raises(tmp_path: Path) -> None:
    """An explicit variant name that does not exist raises a clear error."""
    _write_kconfig_project(tmp_path)
    with pytest.raises(UserNotificationException, match="not found"):
        edit_variant_features(tmp_path, "DoesNotExist", gui=True)


def test_edit_variant_features_no_selection_raises(tmp_path: Path) -> None:
    """Aborting the prompt (no selection) raises rather than opening an editor."""
    _write_kconfig_project(tmp_path)
    with patch("yanga.yview.prompt_user_to_select_option", return_value=None):
        with pytest.raises(UserNotificationException, match="No variant selected"):
            edit_variant_features(tmp_path, None, gui=True)
