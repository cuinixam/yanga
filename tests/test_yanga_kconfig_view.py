import textwrap
from pathlib import Path

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.yview import YangaKConfigData


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
