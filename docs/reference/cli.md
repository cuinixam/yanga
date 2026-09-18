# Command Line Interface

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

* `--project-dir <PATH>`: The directory where the project will be created. Defaults to the current directory.
* `--force`: If set, Yanga will initialize the project even if the target directory is not empty.

## `yanga run`

The most powerful command, `yanga run`, executes the build pipeline. It allows you to build specific variants, components, and targets, and control the pipeline's execution flow.

```bash
yanga run [OPTIONS]
```

**Key Options:**

* `--platform <NAME>`: Specifies the target platform to build for (e.g., `windows`, `linux`).
* `--variant <NAME>`: Selects the product variant to build. If not provided, Yanga will prompt you to choose from the available variants.
* `--component <NAME>`: Narrows the build scope to a single component.
* `--target <NAME>`: Defines a specific build target to execute (e.g., a specific test executable or report).
* `--build-type <TYPE>`: Sets the build type, such as `Debug` or `Release`.
* `--step <NAME>`: Runs the pipeline up to the specified step.
* `--single`: When used with `--step`, it runs only that single step.
* `--force-run`: Forces a step to execute even if it's not considered "dirty" (i.e., its inputs haven't changed).
* `--not-interactive`: Runs in non-interactive mode, failing instead of prompting for user input.
* `--print`: Prints the project's configuration and pipeline steps without executing them.

For more details on pipeline execution, see the [Pipeline Management](./pipeline.md) documentation.

## `yanga gui`

Launches a graphical user interface (GUI) for interacting with Yanga.

```bash
yanga gui [OPTIONS]
```

The GUI provides a visual way to select variants and components, trigger builds, and view results, which can be helpful for development and debugging.

**Arguments:**

* `--project-dir <PATH>`: The project directory to open in the GUI.

## `yanga features`

Shows the product features of all variants, or edits the feature selection of a variant and/or a platform. It runs the `pipeline:` of the `feature_model:` block in the project configuration, and that pipeline's `KConfigEdit` step opens the viewer or the editor (see yanga-core's `feature_model:` and `KConfigEdit` documentation).

```bash
yanga features [OPTIONS]
```

```bash
# All variants side by side (GUI only)
yanga features

# Edit a variant's product selection in the guiconfig GUI editor
yanga features --variant MyVariant

# Use the terminal menuconfig editor instead (works headless, no tkinter needed)
yanga features --variant MyVariant --no-gui

# Edit a variant's selection for one platform, using that platform's feature model
yanga features --variant MyVariant --platform MyPlatform
```

| Flags | Feature model | Opens |
|-------|---------------|-------|
| none | the project's `feature_model:` | the viewer with every variant's product selection |
| `--variant` | the project's `feature_model:` | the editor on the variant's `feature_selection` |
| `--variant` and `--platform` | the platform's `feature_model:` | the editor on the variant's selection for that platform |

The editor saves only into selection files declared in the configuration; a missing declaration is an error. `--platform` without `--variant` is an error too: a platform's model is opened by the platform's own tool, which configures a build of a variant. The viewer or editor runs in the foreground and `yanga` exits when you close it.

**Arguments:**

* `--project-dir <PATH>`: The project directory.
* `--variant <NAME>`: The variant whose selection to edit.
* `--platform <NAME>`: The platform whose feature model to open.
* `--gui` / `--no-gui`: Use the `guiconfig` GUI editor (default) or the terminal `menuconfig`. The view of all variants is GUI only.

## `yanga ide`

Generates project files for Visual Studio Code.

```bash
yanga ide [OPTIONS]
```

This command creates the necessary `.vscode` configuration files (`cmake-kits.json`, `cmake-variants.json`) based on the variants and platforms. This enables a seamless development experience with full IntelliSense, build, and debug support in VS Code.

**Arguments:**

* `--project-dir <PATH>`: The project directory for which to generate IDE files.
