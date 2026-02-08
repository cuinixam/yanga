(pipeline-management)=

# Pipeline Management

Yanga's build process is orchestrated through a configurable pipeline, a sequence of steps defined in your `yanga.yaml` file. This system allows you to automate everything from dependency installation to code generation and compilation.

## Pipeline Configuration

You define the pipeline as a list of stages (e.g., `install`, `gen`, `build`). Each stage contains one or more steps, which are Python classes that perform a specific task.

A typical pipeline configuration looks like this:

```yaml
pipeline:
  - install:
    - step: WestInstall
      module: yanga.steps.west_install
  - gen:
    - step: KConfigGen
      module: yanga.steps.kconfig_gen
  - build:
    - step: GenerateBuildSystemFiles
      module: yanga.steps.execute_build
    - step: ExecuteBuild
      module: yanga.steps.execute_build
```

Each step is defined by its `step` (the class name) and `module` (the Python module where the class is located).

## Pipeline Execution

You run the pipeline using the `yanga run` command. Yanga's smart scheduler determines which steps need to be executed based on whether their inputs have changed or outputs are missing.

* **Run the full pipeline**: `yanga run`
* **Run up to a specific step**: `yanga run --step ExecuteBuild`
* **Run only a single step**: `yanga run --step KConfigGen --single`
* **Force re-execution of steps**: `yanga run --force-run`

## Built-in Pipeline Steps

Yanga includes several pre-built steps to handle common build tasks.

### `WestInstall`

**Module:** `yanga.steps.west_install`

**Purpose:** Manages external Git repository dependencies using `west`.

This step automatically clones and updates repositories defined in `configs` with `id: west` sections within your platform and variant configurations. It's a powerful way to manage third-party libraries and components.

**Configuration:** Add the step to your pipeline. The dependency details are configured in platforms and variants, as described in the [Software Product Line](#product-dependency-management) documentation.

```yaml
pipeline:
  - install:
    - step: WestInstall
      module: yanga.steps.west_install
```

### `ScoopInstall`

**Module:** `yanga.steps.scoop_install`

**Purpose:** Manages Windows-based tool dependencies using `scoop`.

For projects that require specific tools on Windows (like compilers or build tools), this step reads `configs` with `id: scoop` sections from your configuration and ensures the required tools are installed.

**Configuration:** Add the step to your pipeline. Tool dependencies are configured in platforms and variants.

```yaml
pipeline:
  - install:
    - step: ScoopInstall
      module: yanga.steps.scoop_install
```

### `KConfigGen`

**Module:** `yanga.steps.kconfig_gen`

**Purpose:** Processes `KConfig` feature models to generate C header files.

If your project uses a `KConfig` file for feature management, this step generates an `autoconf.h` file containing C macros for all selected features. This allows you to enable or disable code paths using `#ifdef`.

**Configuration:** Add the step to your pipeline, typically in a `gen` stage. The `features_selection_file` is specified in the variant configuration.

```yaml
pipeline:
  - gen:
    - step: KConfigGen
      module: yanga.steps.kconfig_gen
```

### `GenerateBuildSystemFiles`

**Module:** `yanga.steps.execute_build`

**Purpose:** Generates the project's CMake files.

This crucial step translates your `yanga.yaml` configuration into a functional CMake build system. It runs the `cmake_generators` specified in the current platform's configuration to create `CMakeLists.txt` and other necessary files.

**Configuration:** Add this step to your `build` stage, before `ExecuteBuild`. The behavior of this step is controlled by the [CMake Generators](#cmake-generators) defined in your platform configuration.

```yaml
pipeline:
  - build:
    - step: GenerateBuildSystemFiles
      module: yanga.steps.execute_build
```

### `ExecuteBuild`

**Module:** `yanga.steps.execute_build`

**Purpose:** Runs the CMake build process (configure and build).

After the build system files are generated, this step invokes CMake to configure the project and compile your code. It handles passing the correct toolchain file and build type. You can specify a particular build `target` via the `yanga run --target <target_name>` command.

**Configuration:** Add this step to your `build` stage after `GenerateBuildSystemFiles`.

```yaml
pipeline:
  - build:
    - step: ExecuteBuild
      module: yanga.steps.execute_build
```
