# {octicon}`container;1.5em;sd-mr-1` Software Product Line

Yanga provides robust support for managing Software Product Lines (SPL) through its flexible variant and component system. This allows you to define multiple product variants from a common set of assets.

## Variants

Variants are at the core of the SPL support, enabling the definition of distinct products by combining different components and configurations.

### Basic Variant

A minimal variant definition includes a name and a list of components.

```yaml
variants:
  - name: MyVariant
    description: A basic variant.
    components:
      - main
      - comp_a
```

### Feature Selection

For SPLs with feature models (e.g., KConfig), you can specify a feature selection file. This file dictates which features are enabled for the variant, allowing for automated configuration of components based on the selected features.

```yaml
variants:
  - name: FeatureVariant
    components: [main, configurable_feature]
    features_selection_file: "config.txt"
```

````{note}
In case of KConfig, the `features_selection_file` is read by the `KConfigGen` step.

One needs to configure the `KConfigGen` step in the pypeline:

```yaml
pypeline:
  steps:
    - step: KConfigGen
      module: yanga.steps.kconfig_gen
```

````

### Generic Configuration

You can pass custom key-value pairs to the build system using the `config` section. These values are exported as CMake variables in the `config.cmake` generated file.

```yaml
variants:
  - name: ConfigVariant
    components: [main]
    config:
      MY_CUSTOM_FLAG: "enabled"
      BUILD_NUMBER: 123
```

### Platform-Specific Configuration

Yanga allows you to override variant settings for specific platforms. This is useful when a variant requires different components or configuration values depending on the target platform (e.g., `windows` vs. `arm`).

In the example below, `MyVariant` includes the `platform_specific_component` only when built for the `my_platform` platform.

```yaml
variants:
  - name: MyVariant
    components: [main]
    platforms:
      my_platform:
        components: [platform_specific_component]
        config:
          PLATFORM_SPECIFIC_FLAG: "true"
```

(product-dependency-management)=
### Dependency Management

Variants can declare their own external dependencies using `west_manifest` for managing external Git repositories. This ensures that the correct dependencies are fetched and installed for each variant.

```yaml
variants:
  - name: VariantWithDependencies
    components: [main]
    west_manifest:
      remotes:
        - name: gtest
          url-base: https://github.com/google
      projects:
        - name: googletest
          remote: gtest
          revision: v1.16.0
          path: gtest
```

## Component-Based Architecture

Yanga promotes a modular architecture by organizing software into reusable components. Each component is a self-contained unit with its own sources, dependencies, and configurations.

### Basic Component

A minimal component definition requires a name and a list of source files.

```yaml
components:
  - name: my_component
    sources:
      - "src/my_component.c"
```

### Component Location

By default, Yanga resolves component file paths relative to the location of the `yanga.yaml` file that defines it. You can override this by specifying a `path` attribute for a component. This path is interpreted as a directory relative to the project's root, providing greater flexibility in organizing your component sources.

```yaml
components:
  - name: my_component
    # All paths within this component are now relative to 'libs/my_component'
    path: "libs/my_component"
    sources:
      - "src/my_component.c" # Resolved to <project_root>/libs/my_component/src/my_component.c
```

### Include Directories

You can specify include directories for a component, controlling their visibility with a `scope`.
- `PUBLIC` directories are exposed to any component that depends on this one.
- `PRIVATE` directories are only used for compiling this component's sources.

```yaml
components:
  - name: my_library
    sources: ["src/lib.c"]
    include_directories:
      - path: "include"
        scope: PUBLIC
      - path: "src"
        scope: PRIVATE
```

### Component Dependencies

Components can declare dependencies on other components using `required_components`. This ensures that the necessary include directories from dependencies are made available during compilation.

```yaml
components:
  - name: main_app
    sources: ["src/main.c"]
    required_components:
      - my_library
```

### Testing

Yanga provides a dedicated section for test-related configurations. You can specify test sources and enable features like mocking.

```yaml
components:
  - name: my_component
    sources: ["src/my_component.c"]
    testing:
      sources:
        - "test/test_my_component.cpp"
      mocking:
        enabled: true
        strict: true
```

````{note}
The `mocking` feature configuration depends on the mocking generator. In case of the `gtest` mocking framework, you need to configure the `GTestCMakeGenerator` for your platform:

```yaml
platforms:
  - name: gtest
      description: Build and run components GTest tests
      cmake_generators:
        - step: GTestCMakeGenerator
          module: yanga.cmake.gtest
          config:
              mocking:
                # Enable or disable auto-mocking support
                enabled: true
                # Control if any parsing errors are fatal
                strict: false
                # Patterns for symbols to exclude from mocking
                exclude_symbol_patterns:
                  - "_*"
```

````


### Container Components (🚧to be implemented🚧)

For better organization, you can create "container" components that group other components together. This simplifies variant definitions by allowing you to include a single container instead of a long list of individual components.

```yaml
components:
  - name: all_features
    # This component has no sources, it only groups others
    components:
      - feature_a
      - feature_b
```
A variant can then be defined more concisely:
```yaml
variants:
  - name: FullFeatureVariant
    components:
      - main
      - all_features
```

## Reports

There are several CMakeGenerators available to generate reports relevant for a component or a variant.

### Component Reports

For a component there are multiple documentation sources generated and collected:

* user defined component documentation (e.g., `docs/*.md` files)
* source code documentation (e.g., productive and test code) - for every source file a separate markdown file is generated using the `clanguru` Python package
* static analysis reports - `cppcheck` xml report is converted to markdown
* test execution report - the `GoogleTest` JUnit report is converted to markdown
* code coverage report - the `gcovr` markdown report

These files are collected and configured to be processed by Sphinx to generate a single HTML documentation for the component.

There is a dependency between the different build targets to ensure that the reports are generated in the correct order.

The `<component>_report` target depends on:

* `<component>_docs` - to generate the documentation from the source code and user defined documentation
* `<component>_lint` - to generate the static analysis report
* `<component>_coverage` - to generate the code coverage report

All these targets depend on the component build target `<component>_build` to ensure that the component is built before generating the reports.
