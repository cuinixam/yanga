import textwrap
from pathlib import Path

from yanga.ybuild.config import YangaConfig


def test_from_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """\
    pipeline:
        install:
            - stage: YangaInstall
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
    config = YangaConfig.from_file(config_file)
    assert config.pipeline["install"][0].stage == "YangaInstall"
    assert config.pipeline["install"][1].stage == "MyInstall"
