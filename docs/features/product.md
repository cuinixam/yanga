# {octicon}`container;1.5em;sd-mr-1` Software Product Line

## Product Variants

Facilitate the creation and management of different product variants, each with its components and specific configurations.

```{code-block} yaml
variants:
  - name: EnglishVariant
    description: Say hello in English.
    components:
      - main
      - greeter
  - name: GermanVariant
    description: Say hello in German.
    components:
      - main
      - greeter
    features_selection_file: "config_de.txt"
```

## Component-Based Architecture

Organize your software into reusable components to enhance modularity and reusability.

```{code-block} yaml
components:
  - name: main
    type: component
    sources:
      - main.c
  - name: greeter
    type: component
    sources:
      - greeter.c
    test_sources:
      - greeter_test.cc
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
