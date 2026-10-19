# How to Add Component Tests

This guide shows how to configure unit testing for your Yanga components using Google Test.

## Prerequisites

- A Yanga project with at least one component
- A test platform configured with `GTestCMakeGenerator`

## Steps

### 1. Configure a test platform

Add a platform with the `GTestCMakeGenerator`:

```yaml
platforms:
  - name: gtest
    description: Build and run component tests
    generators:
      - step: GTestCMakeGenerator
        module: yanga.cmake.gtest
        config:
          mocking:
            enabled: true
            strict: false
            exclude_symbol_patterns:
              - "_*"
```

### 2. Add test sources to your component

Define a `testing` section in your component configuration:

```yaml
components:
  - name: my_component
    sources: ["src/my_component.c"]
    testing:
      sources:
        - "test/test_my_component.cpp"
```

### 3. Enable auto-mocking (optional)

To automatically generate mocks for component dependencies:

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

### 4. Run the tests

Build and run tests for your component:

```bash
yanga run --platform gtest --target my_component_test
```

Or run all tests:

```bash
yanga run --platform gtest
```

### 5. Test several components together (optional)

To test how components work together, create an integration component that lists them with `integrates` and select it on the test platform:

```yaml
components:
  - name: test_integrations_networking
    integrates: [tcp, udp]
    testing:
      sources:
        - "test/test_networking_integration.cpp"
```

The integration component compiles the sources of `tcp` and `udp` again into its own test executable without selecting them. Automock then mocks only the calls that leave the group, and the coverage stays separate from the components' unit tests. Run it with `yanga run --platform gtest --target test_integrations_networking_test`.

## See also

- [Software Product Line Reference](../reference/product.md) for component configuration
- [CMake Generators](../reference/cmake.md) for GTestCMakeGenerator options
