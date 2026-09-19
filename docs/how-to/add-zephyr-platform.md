# Add a Zephyr platform

Zephyr owns the build: `find_package(Zephyr)` sets up the toolchain, devicetree and Kconfig before `project()`. yanga contributes the variant as a generated `variant.cmake` and drives `west` through the steps in `yanga.zephyr`. Install them with the extra:

```bash
pip install "yanga[zephyr]"
```

The extra brings Zephyr's build-time Python packages. `west` comes with yanga already. Board tools such as `esptool` stay in your project.

## The CMake entry point

The `CMakeLists.txt` that `west build` configures must call `find_package(Zephyr)` before `project()` and include the generated variant after it:

```cmake
cmake_minimum_required(VERSION 3.20)
find_package(Zephyr REQUIRED HINTS ${ZEPHYR_BASE})
project(app C ASM CXX)
include("${CMAKE_BINARY_DIR}/variant.cmake")
```

`ZephyrBuild` passes `-DVARIANT` and `-DPLATFORM` like yanga's own CMake runner; the file may use them or not.

## Pipeline

Zephyr needs its own west workspace and `ZEPHYR_BASE` in the environment before the env setup script is written. Keep this order:

```yaml
pipeline:
  - step: WestInstall
    module: yanga_core.steps.west_install
    config:
      workspace_dir: .yanga/zephyr
      revision_scoped_paths: true
  - step: ZephyrSetup
    module: yanga.zephyr.steps
  - step: GenerateEnvSetupScript
    module: pypeline.steps.env_setup_script
  - step: KConfigGen
    module: yanga_core.steps.kconfig_gen
  - step: GenerateBuildSystemFiles
    module: yanga.cmake.steps
  - step: ZephyrBuild
    module: yanga.zephyr.steps
    config:
      board: native_sim/native/64
      toolchain: host
      kconfig_root: Kconfig.platform
```

Put it on a platform (`platforms: - pipeline:`) when other platforms build differently, or on the project when every variant targets Zephyr.

`workspace_dir` gives Zephyr a west workspace of its own. A workspace holds one manifest, and `WestInstall` writes it from the configs of whichever platform ran last. Other platforms use west only to clone, so that does not matter to them. Zephyr keeps reading the manifest afterwards: `west build`, `west flash` and `west blobs` are extension commands discovered from its `west-commands` entry, and Zephyr's CMake finds modules such as vendor HALs through it. Sharing the default workspace with a non-Zephyr platform would lose those on the next build. An SPL whose platforms all target Zephyr can leave `workspace_dir` out.

## `ZephyrBuild` config

| Key | Required | Meaning |
| --- | --- | --- |
| `board` | yes | Zephyr board, for example `esp32h2_devkitm/esp32h2` |
| `toolchain` | yes | `ZEPHYR_TOOLCHAIN_VARIANT`: `host` or `cross-compile` |
| `kconfig_root` | yes | The platform feature model, relative to the project root. Always passed, because Zephyr's default `<app dir>/Kconfig` matches yanga's `KConfig` on a case-insensitive disk |
| `app_config_dir` | no, `.` | Zephyr's `APPLICATION_CONFIG_DIR`: `prj.conf`, `boards/` |
| `source_dir` | no, `.` | The directory holding the `CMakeLists.txt` above |
| `toolchain_app` | cross-compile | The poks app providing the toolchain; its name is the compiler prefix |
| `sysroot` | no | Sysroot relative to the toolchain root, when Zephyr's detection composes a wrong path |

`--target flash` runs `west flash`; any other target goes to `west build -t`.

## Platform configs

- `west`: the workspace manifest with the `zephyr` project and its `west-commands`.
- `vars` and `cmake`: optional, as on any platform. A `cmake` file is included at the end of `variant.cmake`; use it for Zephyr-side settings that are not components, such as `target_sources(app PRIVATE src/main.c)`.
- One platform per board. Board conf and overlay files live under `<app_config_dir>/boards/`.

## Generators

Replace `CreateExecutableCMakeGenerator` with `ZephyrCMakeGenerator`: the component libraries link into Zephyr's `app` library instead of a yanga executable.

```yaml
generators:
  - step: ZephyrCMakeGenerator
    module: yanga.zephyr.cmake
  - step: ObjectsDepsCMakeGenerator
    module: yanga.cmake.objects_deps
```

## Editing platform features

Zephyr's Kconfig tree only loads inside a Zephyr build, so the platform feature model opens through `ZephyrFeatures`, which runs Zephyr's editor and writes the changes into the variant's `feature_selection` file for that platform. Every variant that builds on the platform needs that file declared:

```yaml
platforms:
  - name: zephyr_sim
    feature_model:
      file: Kconfig.platform
      pipeline:
        - step: ZephyrFeatures
          module: yanga.zephyr.steps
          config:
            board: native_sim/native/64
            toolchain: host
            kconfig_root: Kconfig.platform
```

The build merges that file as `EXTRA_CONF_FILE` on top of `prj.conf`.
