import textwrap
from pathlib import Path

from yanga.project.config import YangaUserConfig


def test_load_pipeline_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """\
    pipeline:
        install:
            - stage: YangaScoopInstall
            - stage: MyInstall
              file: user/install.py
              class: CustomInstall
        build:
            - stage: MyPreBuild
              file: user/build.py
              class: CustomPreBuild
            - stage: YangaBuild
            - stage: MyPostBuild
              file: user/build.py
              class: CustomPostBuild
        deploy:
            - stage: YangaDeploy
    """
        )
    )
    config = YangaUserConfig.from_file(config_file)
    assert config.pipeline
    assert config.pipeline["install"][0].stage == "YangaScoopInstall"
    assert config.pipeline["install"][1].stage == "MyInstall"
    assert config.file == config_file, "file name should be automatically added to config"


def test_load_user_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """\
    components:
      - name: main
        type: component
        sources:
          - main.c

    variants:
      - name: EnglishVariant
        description: Say hello in English.
        bom:
          components:
            - main
      - name: GermanVariant
        description: Say hello in German.
        bom:
          components:
            - main
        config_file: "config_de.txt"

    pipeline:
      install:
        - stage: YangaScoopInstall
          description: Install dependencies
          timeout_sec: 120
      gen:
        - stage: YangaKConfigGen
      build:
        - stage: YangaBuildConfigure
        - stage: YangaBuildRun

    """
        )
    )
    config = YangaUserConfig.from_file(config_file)
    assert config.variants
    de_variant = next((v for v in config.variants if v.name == "GermanVariant"), None)
    assert de_variant
    assert de_variant.config_file == "config_de.txt"
    en_variant = next((v for v in config.variants if v.name == "EnglishVariant"), None)
    assert en_variant
    assert en_variant.config_file is None
