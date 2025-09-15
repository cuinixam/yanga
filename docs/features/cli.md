# {octicon}`terminal;1.5em;sd-mr-1` Command Line Interface

Yanga provides a command-line interface (CLI) to manage your projects, run builds, and interact with the ecosystem. All commands are accessed through the main `yanga` executable.

To see a list of all available commands and their options, you can run:

```bash
yanga --help
```

## `yanga init`

Initializes a new Yanga project in a specified directory.

```bash
yanga init [OPTIONS]
```

This command creates the basic directory structure and a default `yanga.yaml` configuration file, getting you started quickly.

**Arguments:**

*   `--project-dir <PATH>`: The directory where the project will be created. Defaults to the current directory.
*   `--force`: If set, Yanga will initialize the project even if the target directory is not empty.

## `yanga run`

The most powerful command, `yanga run`, executes the build pipeline. It allows you to build specific variants, components, and targets, and control the pipeline's execution flow.

```bash
yanga run [OPTIONS]
```

**Key Options:**

*   `--platform <NAME>`: Specifies the target platform to build for (e.g., `windows`, `linux`).
*   `--variant-name <NAME>`: Selects the product variant to build. If not provided, Yanga will prompt you to choose from the available variants.
*   `--component-name <NAME>`: Narrows the build scope to a single component.
*   `--target <NAME>`: Defines a specific build target to execute (e.g., a specific test executable or report).
*   `--build-type <TYPE>`: Sets the build type, such as `Debug` or `Release`.
*   `--step <NAME>`: Runs the pipeline up to the specified step.
*   `--single`: When used with `--step`, it runs only that single step.
*   `--force-run`: Forces a step to execute even if it's not considered "dirty" (i.e., its inputs haven't changed).
*   `--not-interactive`: Runs in non-interactive mode, failing instead of prompting for user input.
*   `--print`: Prints the project's configuration and pipeline steps without executing them.

For more details on pipeline execution, see the [Pipeline Management](./pipeline.md) documentation.

## `yanga gui`

Launches a graphical user interface (GUI) for interacting with Yanga.

```bash
yanga gui [OPTIONS]
```

The GUI provides a visual way to select variants and components, trigger builds, and view results, which can be helpful for development and debugging.

**Arguments:**

*   `--project-dir <PATH>`: The project directory to open in the GUI.

## `yanga view`

Displays the resolved feature configurations for all variants.

```bash
yanga view [OPTIONS]
```

This command is useful for inspecting the final feature set of each variant after processing the KConfig models and feature selection files.

**Arguments:**

*   `--project-dir <PATH>`: The project directory to analyze.

## `yanga ide`

Generates project files for Visual Studio Code.

```bash
yanga ide [OPTIONS]
```

This command creates the necessary `.vscode` configuration files (`cmake-kits.json`, `cmake-variants.json`) based on the variants and platforms. This enables a seamless development experience with full IntelliSense, build, and debug support in VS Code.

**Arguments:**

*   `--project-dir <PATH>`: The project directory for which to generate IDE files.
