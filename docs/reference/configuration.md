# Configuration

The project configuration is defined as `.yaml` files.
YANGA parses all `yanga.yaml` files in the project.
Some directories are excluded while searching for the configuration files (e.g., `.venv`, `.git`, etc.) to avoid unnecessary parsing of files.

One can override the default configuration by providing a custom configuration file. Either by providing a `yanga.ini` file or adding the configuration in the `pyproject.toml` file.

Ini file example:

```{code-block} ini
:linenos:
:name: yanga.ini

[default]
configuration_file_name = build.yaml
exclude_dirs = .git, build, .venv
```

TOML file example:

```{code-block} toml
:linenos:
:name: pyproject.toml

[tool.yanga]
configuration_file_name = "build.yaml"
exclude_dirs = [".git", "build", ".venv"]
```

With the example above, YANGA will look for the `build.yaml` file in the project root directory and exclude the `.git`, `build`, and `.venv` directories while searching for the configuration files.
