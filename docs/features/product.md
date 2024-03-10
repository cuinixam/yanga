# {octicon}`container;1.5em;sd-mr-1` Software Product Line

## Product Variants

Facilitate the creation and management of different product variants, each with its own Bill of Materials (BOM) and specific configurations.

```{code-block} yaml
variants:
  - name: EnglishVariant
    description: Say hello in English.
    bom:
      components:
        - main
        - greeter
  - name: GermanVariant
    description: Say hello in German.
    bom:
      components:
        - main
        - greeter
    config_file: "config_de.txt"
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
