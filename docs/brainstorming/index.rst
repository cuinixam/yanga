Brainstorming
#############

What kind of files are typically found in a C/C++ software repository?
======================================================================

Let's consider a C/C++ application for an embedded system.
In a C/C++ repository, you'll typically find the following types of files:

- Source files
   - These files contain the main implementation of the program or library.
   - They provide the functionality and logic of your software.

- Header files
   - Header files are used to declare functions, classes, and variables that are used across multiple source files. They help in organizing the code and enabling modularity.

- Platform-specific files
   - Code and configuration settings that are specific to the target platform or hardware. They include startup code, linker scripts, memory maps, and other low-level code that interacts directly with the hardware.

- Build system files:
   - These files are used to configure and control the build process, such as specifying dependencies, compiler flags, and target outputs.

- Precompiled libraries
   - Precompiled libraries are collections of compiled code that can be linked into your program. They provide reusable functionality and can speed up the build process.

- Configuration files:
   - Configuration files store settings related to the build environment, compiler flags, and project settings for IDEs. They help in customizing the build process and maintaining consistency across different environments.

- Scripts
   - Scripts automate tasks related to building, testing, and deployment. They can also be used for code generation, formatting, and other development tasks.

- Documentation
   - Documentation files explain the purpose, functionality, and usage of the software. They help other developers understand and maintain the code.

- Test files
   - Unit tests and other tests that verify the correctness and robustness of your software. They help ensure the quality and stability of your codebase.

- Third-party dependencies
   -  external libraries or packages that your software relies on. They provide additional functionality and help reduce the development effort.

- Miscellaneous
   - License files
   - Git configuration files
   - Continuous Integration/Continuous Deployment (CI/CD) configuration files
   - Code style configuration files

- Code generation files:
   - Code generator scripts to automate the code generation process by invoking code generation tools and applying the required settings and input data.
   - Code generator configuration files: These files contain settings and options for code generation tools, such as output directories, file naming conventions, and other customization options.
   - Code templates used by code generators to produce source and header files based on specified configurations or input data.

- Debugging and flashing related files:
   - Debugger configuration files: These files contain settings and options for the debugger, such as target device, connection type, or specific debugger features.
   - Debugger scripts: These scripts can be used to automate certain debugging tasks, such as setting breakpoints, watching variables, or loading memory dumps.
   - Flashing tools configuration files: These files contain settings for flashing tools, such as target device, connection type, memory layout, or specific tool options.
   - Flashing scripts to automate the flashing process by invoking flashing tools and applying the required settings and firmware files.


What kind of actions can be performed on these files?
=====================================================

- Manually writing and editing code:
   - Implementing new features, bug fixes, and improvements
   - Refactoring and optimizing existing code

- Parsing and processing files:
   - Reading and parsing configuration files
   - Reading and processing input data files for code generation
   - Parsing device tree files
   - Processing RTOS and BSP files

- Code generation:
   - Applying templates to generate source and header files
   - Executing code generator scripts
   - Generating files based on input data and configuration settings

- Compilation and linking:
   - Compiling source files into object files
   - Linking object files and libraries into executable or library files
   - Generating debug symbols files

- Debugging:
   - Loading debug symbols files
   - Configuring and launching debugger sessions
   - Executing debugger scripts
   - Analyzing performance profiling files

- Flashing and firmware management:
   - Configuring and executing flashing tools and scripts
   - Loading firmware onto the target device

- Testing and validation:
   - Compiling and running unit tests
   - Executing test scripts and test configuration files
   - Analyzing test results

- Build system and automation:
   - Processing build system files
   - Generating build system files for different configurations (release, debug, tests)
   - Executing build automation scripts

- Documentation and organization:
   - Creating and updating documentation files
   - Organizing files in a structured folder hierarchy

- Generating reports and analysis:
   - Generating code coverage reports
   - Creating static analysis reports (linting, code quality, etc.)
   - Producing memory and performance profiling reports
   - Generating dependency graphs and analysis
   - Creating build logs and error reports
   - Generating test execution reports and test coverage analysis

- Packaging and distribution:
   - Creating binary packages for distribution
   - Generating installation scripts
   - Creating documentation packages (e.g., user manuals, API reference, etc.)
   - Packaging source code for distribution or archiving
   - Generating versioned releases and tags in version control systems

- Version control and CI/CD:
   - Managing files with version control systems (e.g., Git)
   - Configuring and executing CI/CD pipelines


Basic use case
==============

- Developer: Manually editing source files (creating new features, bug fixes, improvements)
- Build system tool: Parsing and processing build system files and configuration files
- Build system tool: Generating build system files for different configurations (release, debug, tests)
- Build system tool: Executing code generation tools and scripts based on configuration files
- Compiler: Pre-process source files
- Compiler: Compiling source files into object files
- Linker: Linking object files and libraries into executable or library files
- Test tool: Compiling and running unit tests
- Test tool: Executing test scripts and test configuration files
- Test tool: Analyzing test results and generating test execution reports
- Build system tool: Generating code coverage reports and static analysis reports
- Build system tool: Producing memory and performance profiling reports
- Build system tool: Generating dependency graphs and analysis
- Build system tool: Creating build logs and error reports
- Packaging tool: Creating binary packages for distribution
- Packaging tool: Generating installation scripts or packages
- Packaging tool: Creating documentation packages (user manuals, API reference, etc.)
- Packaging tool: Packaging source code for distribution or archiving


Software product line engineering (SPLE)
========================================

Software product line engineering (SPLE) is a software engineering methodology that focuses
on the systematic reuse of common assets and the management of variability across a family
of related products :cite:`wiki_spl`.

- Group of similar software products sharing common elements, with unique features built from a shared foundation
- Identifiable traits or functions in software products highlighting similarities and differences across the product line
- Mapping of feature relationships and constraints for the entire software product line
- Visual depiction of feature model using hierarchy and symbols to show connections and restrictions
- Reusable components, like code, documentation, or tests, shared across multiple products in the product line
- Process of discovering, defining, and implementing shared and unique aspects in a software product line, creating core assets and feature models
- Building individual software products within the product line using core assets and feature models from domain engineering
- Distinctions between product variants in the software product line, often shown by optional or alternative features
- Points in software artifacts where product differences can arise, such as through conditional compilation, config flags, or plugins
- Moment in the software development process when a variability point is determined, like at compile-time, build-time, or runtime
- Specific choice of features from a feature model, leading to a distinct software product within the product line
- Shared attributes found in all or most products within the software product line, often represented by mandatory features
- Process of choosing and combining core assets based on a specific configuration to develop an individual software product
- A specific product variant within the product line, characterized by a unique combination of features, resulting from a particular configuration of the feature model.


Folder structure
================

::

   project_root/
   ├─ containers/
   │   ├─ container_A/
   │   │   ├─ components/
   │   │   │   ├─ component_A1/
   │   │   │   │   ├─ include/
   │   │   │   │   └─ src/
   │   │   │   └─ component_A2/
   │   │   │       ├─ include/
   │   │   │       └─ src/
   │   │   └─ configs/
   │   │       └─ (configuration files for container_A)
   │   └─ container_B/
   │       ├─ components/
   │       │   ├─ component_B1/
   │       │   │   ├─ include/
   │       │   │   └─ src/
   │       │   └─ component_B2/
   │       │       ├─ include/
   │       │       └─ src/
   │       └─ configs/
   │           └─ (configuration files for container_B)
   ├─ variants/
   │   ├─ variant_1/
   │   │   └─ (configuration files for variant_1)
   │   └─ variant_2/
   │       └─ (configuration files for variant_2)
   ├─ code_generators/
   │   └─ (code generator specific folders and files)
   ├─ third_party/
   │   └─ (third-party library folders and files)
   ├─ unit_tests/
   │   ├─ test_component_A1/
   │   │   ├─ include/
   │   │   └─ src/
   │   └─ test_component_B1/
   │       ├─ include/
   │       └─ src/
   └─ build_system_generator/
      └─ (build system generator scripts, configuration files, and plugins)



Diagrams
========

.. mermaid:: figures/artifacts.mmd
