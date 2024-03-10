# Concepts and Terminology

## Domain

- Product - a product from a company's product family.
- Variant - a specific configuration of a product required by a customer.
- Component - the basic building block of a product variant.
- Platform - the environment for which the product is built and deployed.
- Assembly line - the process of building and deploying a product variant for a specific platform.

## Concepts

### Multi-Pipeline Orchestration

Consider the following table, which outlines the necessity of different pipeline configurations for developing, testing and releasing a software product:

|       | Build | Run | Release |
| ----- | ----- | --- | ------- |
| exe   | ✅    | ✅  |         |
| gtest | ✅    | ✅  |         |
| hil   | ✅    | ✅  |         |
| ecu   | ✅    |     | ✅💰    |

- **exe**: build and run the software on a simulated environment.
- **gtest**: build and run unit tests.
- **hil**: specific hardware-in-the-loop (HIL) testing.
- **ecu**: actual hardware deployment for the customer (release). This is where the 💰 is made.

YANGA allows for the configuration of necessary steps to build and release the software for a specified platform and use case (means every individual line in the table above).

:::{important}
YANGA currently does not support orchestrating multiple pipelines concurrently.
Multi-pipeline orchestration would enable simultaneous management and execution of several build and deployment processes.
:::
