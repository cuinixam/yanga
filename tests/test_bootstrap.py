import runpy
import sys
from pathlib import Path

from yanga.commands.init import ProjectBuilder
from yanga.commands.project_templates.template.bootstrap_j2 import (
    CreateVirtualEnvironment,
    PyPiSourceParser,
)


def test_pypi_source_from_toml():
    pyproject_toml_content = """
[[tool.poetry.source]]
name = "my_pypi"
url = "https://pypi.org/simple"
"""
    pypi_source = PyPiSourceParser.from_pyproject_toml_content(pyproject_toml_content)
    assert pypi_source
    assert pypi_source.name == "my_pypi"
    assert pypi_source.url == "https://pypi.org/simple"

    pyproject_toml_content = """
[tool.poetry.source]
name = my_pypi
url = "https://pypi.org/simple"
"""
    pypi_source = PyPiSourceParser.from_pyproject_toml_content(pyproject_toml_content)
    assert pypi_source
    assert pypi_source.name == "my_pypi"
    assert pypi_source.url == "https://pypi.org/simple"


def test_create_pip_ini_simple(tmp_path: Path) -> None:
    venv_dir = tmp_path / ".venv"
    scripts_dir = venv_dir.joinpath("Scripts" if sys.platform.startswith("win32") else "bin")
    scripts_dir.mkdir(parents=True)
    my_venv = CreateVirtualEnvironment.instantiate_os_specific_venv(venv_dir)
    my_venv.pip_configure("https://my.pypi.org/simple/stable", True)
    pip_ini = scripts_dir / "pip.ini"
    assert pip_ini.exists()
    assert (
        pip_ini.read_text()
        == """\
[global]
index-url = https://my.pypi.org/simple/stable
trusted-host = my.pypi.org
"""
    )


def test_create_pip_ini(tmp_path: Path) -> None:
    project_dir = tmp_path
    builder = ProjectBuilder(project_dir)
    builder.with_cookiecutter_dir("template").with_jinja_template(
        "template/bootstrap_j2.py", "bootstrap.py"
    ).with_jinja_template("common/poetry.toml", "poetry.toml").with_template_config_file("template/cookiecutter.json")
    builder.build()
    # Add pypi source to pyproject.toml
    pyproject_toml = project_dir / "pyproject.toml"
    pyproject_toml.write_text(
        """[[tool.poetry.source]]
name = "my_pypi"
url = "https://pypi.org/simple"
"""
        + pyproject_toml.read_text()
    )

    bootstrap_py = tmp_path.joinpath("bootstrap.py")
    assert bootstrap_py.exists()
    # Execute the main function in the bootstrap.py script using runpy
    runpy.run_path(bootstrap_py.as_posix(), run_name="__test_main__")

    assert project_dir.joinpath(".venv", "Scripts" if sys.platform.startswith("win32") else "bin", "pip.ini").exists()
