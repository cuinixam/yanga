# {octicon}`cpu;1.5em;sd-mr-1` Platform Configuration

Yanga's platform configuration allows you to define target-specific build environments, toolchains, and dependencies. This ensures that your project can be built consistently across different hardware, operating systems, or custom environments.

## Basic Platform

A platform definition requires a `name`. You can also provide a `description` and specify a `toolchain_file` for cross-compilation or environment-specific compiler settings.

```yaml
platforms:
  - name: native
    description: Build for the host system.
    toolchain_file: "toolchains/native.cmake"
```

## Build Types

You can restrict the build types (e.g., `Debug`, `Release`) that are valid for a specific platform. This is useful if a platform only supports a subset of build configurations.

```yaml
platforms:
  - name: embedded_target
    toolchain_file: "toolchains/arm-gcc.cmake"
    build_types:
      - Debug
      - Release
```

## CMake Generators

Each platform can have a unique pipeline of `cmake_generators`. These are steps that generate different parts of the CMake build system, such as executables, libraries, or test harnesses.

```yaml
platforms:
  - name: windows_test
    description: Build and run tests on Windows
    cmake_generators:
      - step: GTestCMakeGenerator
        module: yanga.cmake.gtest
```

See the [CMake Generators](#cmake-generators) documentation for more details on available generators and their configurations.

## Platform-Specific Dependencies

Platforms can define their own dependencies, which are essential for setting up the build environment. Yanga uses `west` to manage Git repository dependencies and `scoop` to manage tools and packages on Windows.

### West Manifest

For platforms that require external Git-based dependencies, you can include a `west_manifest`. This allows you to specify repositories, remotes, and revisions, and `yanga` will ensure they are cloned and updated correctly.

```yaml
platforms:
  - name: my_platform_with_deps
    west_manifest:
      remotes:
        - name: my-remote
          url-base: https://github.com/my-org
      projects:
        - name: my-library
          remote: my-remote
          revision: v2.1.0
          path: vendor/my-library
```

### Scoop Manifest

For Windows-based platforms, you can use a `scoop_manifest` to ensure the necessary development tools are available.

```yaml
platforms:
  - name: windows_dev
    scoopy_manifest:
      apps:
        - name: git
        - name: ninja
```
