from pathlib import Path

from py_app_dev.core.docs_utils import validates

from yanga.ybuild.variant import VariantConfig


@validates(
    "REQ-VARIANT_NAME-0.0.1",
    "REQ-VARIANT_SLUG-0.0.1",
    "REQ-VARIANT_DESCRIPTION-0.0.1",
    "REQ-VARIANT_TAGS-0.0.1",
)
def test_variant_config_from_yaml(tmp_path: Path) -> None:
    variant_config_file = tmp_path / "variant.yaml"
    variant_config_file.write_text(
        """
        name: MyVar
        description: MyVar description
        tags:
            - tag1
            - tag2
        """
    )
    variant = VariantConfig.from_yaml(variant_config_file.read_text())
    assert variant.name == "MyVar"
    assert variant.slug == "myvar"
    assert variant.tags == ["tag1", "tag2"]
    assert variant.description == "MyVar description"
    variant.slug = "mY_SluG"
    assert variant.slug == "my_slug"


@validates("REQ-VARIANT_NAME-0.0.1")
def test_variant_name():
    variant = VariantConfig("Test")
    assert variant.name == "Test"
