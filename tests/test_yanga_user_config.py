import textwrap
from pathlib import Path

from yanga.domain.config import YangaUserConfig


def test_load_pipeline_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """\
    pipeline:
        install:
            - step: ScoopInstall
              module: yanga.steps.scoop_install
            - step: MyInstall
              file: user/install.py
              class: CustomInstall
        build:
            - step: MyPreBuild
              file: user/build.py
              class: CustomPreBuild
            - step: ExecuteBuild
              module: yanga.steps.execute_build
            - step: MyPostBuild
              file: user/build.py
              class: CustomPostBuild
        deploy:
            - step: YangaDeploy
    """
        )
    )
    config = YangaUserConfig.from_file(config_file)
    assert config.pipeline and isinstance(config.pipeline, dict)
    assert config.pipeline["install"][0].step == "ScoopInstall"
    assert config.pipeline["install"][1].step == "MyInstall"
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
        - step: ScoopInstall
          module: yanga.steps.scoop_install
          description: Install dependencies
          timeout_sec: 120
      gen:
        - step: KConfigGen
          module: yanga.steps.kconfig_gen
      build:
        - step: GenerateBuildSystemFiles
          module: yanga.steps.execute_build
        - step: ExecuteBuild
          module: yanga.steps.execute_build

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
