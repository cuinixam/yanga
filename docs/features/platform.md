# {octicon}`cpu;1.5em;sd-mr-1` Platform Configuration

Supports the configuration of multiple platforms, including the setup of custom build environments and toolchains.

```{code-block} yaml
:emphasize-lines: 2,9
platforms:
  - name: win_exe
    description: Build Windows executable
    cmake_generators:
      - step: CMakeGenerator
        module: yanga.cmake.executable
    toolchain_file: clang.cmake
    is_default: true
  - name: gtest
    description: Build GTest tests
    cmake_generators:
      - step: GTestCMakeGenerator
        module: yanga.cmake.gtest
    toolchain_file: gcc.cmake
```
