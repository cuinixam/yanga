# How to Create a Product Variant

This guide shows how to define and configure a product variant in Yanga.

## Prerequisites

- A Yanga project with at least one component defined

## Steps

### 1. Define a basic variant

Add a variant to your `yanga.yaml`:

```yaml
variants:
  - name: MyProduct
    description: My product variant
    components:
      - main
      - feature_a
```

### 2. Add configuration values (optional)

Pass custom key-value pairs to the build system:

```yaml
variants:
  - name: MyProduct
    components: [main]
    configs:
      - id: vars
        content:
          MY_CUSTOM_FLAG: "enabled"
          BUILD_NUMBER: 123
```

These values are exported as CMake variables in `config.cmake`.

### 3. Use feature selection (optional)

For projects using KConfig feature models:

```yaml
variants:
  - name: MyProduct
    components: [main, configurable_feature]
    features_selection_file: "config.txt"
```

:::{note}
This requires the `KConfigGen` step in your pipeline.
:::

### 4. Add platform-specific overrides (optional)

Customize the variant for specific platforms:

```yaml
variants:
  - name: MyProduct
    components: [main]
    platforms:
      embedded:
        components: [embedded_driver]
        configs:
          - id: vars
            content:
              TARGET_EMBEDDED: "true"
```

### 5. Build the variant

```bash
yanga run --variant MyProduct --platform native
```

## See also

- [Software Product Line Reference](../reference/product.md) for full configuration schema
- [Platform Configuration](../reference/platform.md) for platform setup
