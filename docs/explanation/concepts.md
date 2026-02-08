# Concepts and Terminology

## Domain

- Product - a product from a company's product family.
- Variant - a specific configuration of a product required by a customer.
- Component - the basic building block of a product variant.
- Platform - the environment for which the product is built and deployed.
- Assembly line - the process of building and deploying a product variant for a specific platform.

## Concepts

### Extensible Architecture

YANGA is designed with an extensible architecture that allows users to customize and enhance its functionality through extensions written in Python.

Extension points:

- custom pipeline steps - see [Pipeline Management](#pipeline-management)
- custom CMake generators - see [CMake Generators](#cmake-generators)


### Reporting

YANGA provides built-in reporting CMake generator which collects all report relevant information and renders it into HTML files using Sphinx.
Every pipeline step or CMake generator can contribute to the report by registering report relevant files:

- markdown files: these files are rendered into HTML using Sphinx
- raw html files: these files are directly included into the final report without any processing
