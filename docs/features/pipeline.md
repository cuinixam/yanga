# {octicon}`workflow;1.5em;sd-mr-1` Pipeline Management

## Pipeline Configuration

Define and manage pipelines for installation, generation, building, and publishing phases with ease.

```{code-block} yaml
pipeline:
  - install:
    - step: ScoopInstall
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: Build
```

One can **extend** the pipeline with custom steps. The pipeline is executed in the order defined in the configuration file.

```{code-block} yaml
:emphasize-lines: 9-10
pipeline:
  - install:
    - step: ScoopInstall
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: Build
  - publish:
    - step: Artifactory
```

Pipeline steps can be **replaced** with custom steps.

```{code-block} yaml
:emphasize-lines: 8
pipeline:
  - install:
    - step: ScoopInstall
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: MyNewBuild
  - publish:
    - step: Artifactory
```

## Pipeline Execution

**Execution order**

All the steps in the pipeline are executed in the order defined in the configuration file.

**Execution context**

The execution context is passed to each step in the pipeline. The context contains the configuration, the environment, and the state of the pipeline.
Every step can modify the context to register new information or to modify the state of the pipeline.

**Dependency management**

Every step can define its dependencies. The pipeline executor will only run a step only if its dependencies have been changed or one of its outputs is missing.

**Single step execution**

It is possible to execute a single step in the pipeline. This is useful for debugging or for testing a single step.

For more details check the `run` command.

```{code-block} bash
yanga run --help
```

## Yanga Pypeline Steps

### Install Scoop Dependencies Step

The `ScoopInstall` step provides support for platform-specific and variant-specific scoop dependencies, allowing SPL builds to install only the tools needed for specific platforms or variants rather than installing all tools for all platforms.

#### Features

- **Platform-Specific Tools**: Install different tools based on the target platform
- **Variant-Specific Tools**: Install additional tools for specific build variants
- **Global Dependencies**: Support for shared tools across all builds via `scoopfile.json`
- **Conflict Resolution**: Automatic deduplication of dependencies across sources
- **Efficient Builds**: Only installs tools needed for the specific platform/variant combination

#### Configuration

The step supports three levels of scoop dependency configuration:

**Global Dependencies** (optional)
```{code-block} json
:caption: scoopfile.json
{
  "buckets": [
    {
      "name": "main",
      "source": "https://github.com/ScoopInstaller/Main"
    }
  ],
  "apps": [
    {
      "name": "git",
      "source": "main"
    }
  ]
}
```

**Platform-Specific Dependencies**
```{code-block} yaml
:caption: Platform configuration
platforms:
  - name: windows_msvc
    description: Windows build with MSVC
    scoop_manifest:
      buckets:
        - name: main
          source: https://github.com/ScoopInstaller/Main
      apps:
        - name: msvc-build-tools
          source: main

  - name: windows_clang
    description: Windows build with Clang
    scoop_manifest:
      buckets:
        - name: versions
          source: https://github.com/ScoopInstaller/Versions
      apps:
        - name: mingw-winlibs-llvm-ucrt
          source: versions
```

**Variant-Specific Dependencies**
```{code-block} yaml
:caption: Variant configuration
variants:
  - name: debug_variant
    platform: windows_clang
    scoop_manifest:
      buckets:
        - name: main
          source: https://github.com/ScoopInstaller/Main
      apps:
        - name: cppcheck
          source: main
```

#### Pipeline Integration

```{code-block} yaml
:caption: Pipeline configuration
pipeline:
  install:
    - step: ScoopInstall
      module: yanga.steps.scoop_install
```

### Install West Dependencies Step

The `WestInstall` step provides support for platform-specific and variant-specific West dependencies for Zephyr projects. West is a meta-repository management tool that helps manage multiple Git repositories as part of a larger project. This step allows SPL builds to install only the dependencies needed for specific platforms or variants.

#### Features

- **Platform-Specific Dependencies**: Install different repositories based on the target platform
- **Variant-Specific Dependencies**: Install additional repositories for specific build variants
- **Global Dependencies**: Support for shared dependencies across all builds via `west.yaml`
- **Automatic Merging**: Combines dependencies from global, platform, and variant configurations
- **Shared External Directory**: All variants share the same external dependencies directory for efficiency

#### Configuration

The step supports three levels of West dependency configuration:

**Global Dependencies** (optional)
```{code-block} yaml
:caption: west.yaml
manifest:
  remotes:
    - name: zephyrproject-rtos
      url-base: https://github.com/zephyrproject-rtos
  projects:
    - name: zephyr
      remote: zephyrproject-rtos
      revision: main
      path: zephyr
```

**Platform-Specific Dependencies**
```{code-block} yaml
:caption: Platform configuration
platforms:
  - name: nrf52840dk
    description: Nordic nRF52840 DK platform
    west_manifest:
      remotes:
        - name: nordicsemi
          url_base: https://github.com/nrfconnect
      projects:
        - name: sdk-nrf
          remote: nordicsemi
          revision: v2.5.0
          path: nrf

  - name: esp32_devkit
    description: ESP32 development kit platform
    west_manifest:
      remotes:
        - name: espressif
          url_base: https://github.com/espressif
      projects:
        - name: esp-idf
          remote: espressif
          revision: v5.1.1
          path: esp-idf
```

**Variant-Specific Dependencies**
```{code-block} yaml
:caption: Variant configuration
variants:
  - name: debug_variant
    platform: nrf52840dk
    west_manifest:
      remotes:
        - name: googletest
          url_base: https://github.com/google
      projects:
        - name: googletest
          remote: googletest
          revision: v1.14.0
          path: external/gtest
```

#### Pipeline Integration

```{code-block} yaml
:caption: Pipeline configuration
pipeline:
  install:
    - step: WestInstall
      module: yanga.steps.west_install
```
