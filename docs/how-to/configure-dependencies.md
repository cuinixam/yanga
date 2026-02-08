# How to Configure Variant Dependencies

This guide shows how to manage external Git repository dependencies for your Yanga variants using West.

## Prerequisites

- A Yanga project with at least one variant defined
- The `WestInstall` step configured in your pipeline

## Steps

### 1. Add the WestInstall step to your pipeline

Ensure your pipeline includes the `WestInstall` step in the `install` stage:

```yaml
pipeline:
  - install:
    - step: WestInstall
      module: yanga.steps.west_install
```

### 2. Define dependencies in your variant

Add a `configs` section with `id: west` to your variant configuration:

```yaml
variants:
  - name: MyVariant
    components: [main]
    configs:
      - id: west
        content:
          remotes:
            - name: gtest
              url-base: https://github.com/google
          projects:
            - name: googletest
              remote: gtest
              revision: v1.16.0
              path: gtest
```

### 3. Add platform-specific dependencies (optional)

If a dependency is only needed for a specific platform, define it in the platform-specific section:

```yaml
variants:
  - name: MyVariant
    components: [main]
    platforms:
      my_platform:
        configs:
          - id: west
            content:
              remotes:
                - name: platform_specific_remote
                  url-base: https://github.com/platform-specific
              projects:
                - name: platform_specific_lib
                  remote: platform_specific_remote
                  revision: v1.0.0
                  path: external/platform_lib
```

### 4. Run the pipeline

Execute `yanga run` to install dependencies:

```bash
yanga run
```

West will clone the repositories to the specified paths.

## See also

- [Software Product Line Reference](../reference/product.md) for full configuration schema
- [Pipeline Management](../reference/pipeline.md) for WestInstall step details
