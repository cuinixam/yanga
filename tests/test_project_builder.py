from pathlib import Path

from yanga.commands.init import ProjectBuilder


def test_jinja_template_rendering(tmp_path: Path) -> None:
    builder = ProjectBuilder(project_dir=tmp_path)
    builder.with_jinja_template("template/bootstrap_j2.ps1", "bootstrap.ps1").with_jinja_template(
        "template/bootstrap_j2.py", "bootstrap.py"
    ).with_template_config_file("template/cookiecutter.json")
    builder.build()
    assert tmp_path.joinpath("bootstrap.ps1").exists()
    assert tmp_path.joinpath("bootstrap.py").exists()
    assert "poetry>=1.7.1" in tmp_path.joinpath("bootstrap.py").read_text()
