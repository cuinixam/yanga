Build System Generator
######################

CMake Generated Files for Building Software Variants
====================================================

Overview
--------
This suite of CMake files (``CMakeLists.txt``, ``variant.cmake``, ``components.cmake``) provides a structured approach to build a specific software variant, ``<variant_name>``.
The structure allows for modular management of project configuration, component definitions, and test orchestration.

CMake Structure Diagram
-----------------------
.. mermaid::

    graph TD
        A[CMakeLists.txt] -->|includes| B[variant.cmake]
        B -->|sets project and compiler configs| C[Project Configuration]
        B -->|includes| D[components.cmake]
        D -->|defines components and test targets| E[Component Libraries]
        D -->|defines custom test targets| F[Custom Test Targets]
        B -->|configures executable and tests| G[Executable and Test Configuration]

CMakeLists.txt
--------------
**Minimum CMake Version and Inclusion of Variant Configuration**:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.20)
    include(${CMAKE_CURRENT_LIST_DIR}/variant.cmake)

Specifies the minimum version of CMake and includes the ``variant.cmake`` file for detailed project configuration.

variant.cmake
-------------
**Project Configuration and Compiler Settings**:

.. code-block:: cmake

    project(<variant_name>)
    set(CMAKE_CXX_STANDARD 99)
    set(CMAKE_C_COMPILER clang)
    set(CMAKE_CXX_COMPILER clang++)

Sets the variant name, C++ standard, and compilers.

**Component Inclusion and Additional Settings**:

.. code-block:: cmake

    set(SOURCE_FILES )
    include(${CMAKE_CURRENT_LIST_DIR}/components.cmake)
    include_directories(<list-of-include-directories>)

Initializes the source files, includes the ``components.cmake`` for component-specific configurations, and specifies directories for the compiler to find headers.

**Executable Target and Test Configuration**:

.. code-block:: cmake

    add_executable(${PROJECT_NAME} ${SOURCE_FILES} ...)
    execute_process(
        COMMAND ${CMAKE_COMMAND} -S ${CMAKE_CURRENT_LIST_DIR}/test -B ${CMAKE_CURRENT_LIST_DIR}/test/build -G Ninja
        RESULT_VARIABLE result
    )
    if(result)
        message(FATAL_ERROR "CMake step for test failed: ${result}")
    endif()

Defines the executable target for the project and configures the test project. It also checks for errors in the test configuration step.

components.cmake
----------------
**Component Libraries and Test Targets**:

.. code-block:: cmake

    set(component <component_name>)
    add_library(${component}_lib OBJECT <path-to-component-source>)
    add_custom_target(${component}_test
        COMMAND ${CMAKE_COMMAND} --build ${CMAKE_CURRENT_LIST_DIR}/test/build --target ${component}_test
        COMMENT "Running ${component}_test"
    )

Repeats the above block for each component, creating libraries and corresponding test targets.

CMake Generated Files for Testing Software Variants
===================================================

Overview
--------
This collection of CMake files (``CMakeLists.txt``, ``variant.cmake``, ``components.cmake``) is configured to facilitate the testing of a software variant, ``<variant_name>``.
The setup integrates GoogleTest for unit testing and includes mechanisms for building test executables and generating reports.

CMake Testing Structure Diagram
-------------------------------
.. mermaid::

    graph TD
        A[CMakeLists.txt] -->|includes| B[variant.cmake]
        B -->|sets project and compiler configs| C[Project Configuration]
        B -->|includes| D[components.cmake]
        D -->|defines test executables| E[Test Executables]
        D -->|sets up test reporting| F[Test Reporting]
        B -->|configures test framework| G[Test Framework Configuration]

CMakeLists.txt
--------------
**Minimum CMake Version and Inclusion of Variant Configuration**:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.20)
    include(${CMAKE_CURRENT_LIST_DIR}/variant.cmake)

Specifies the minimum version of CMake and includes the ``variant.cmake`` file for detailed project testing configuration.

variant.cmake
-------------
**Project Configuration, Compiler and GoogleTest Settings**:

.. code-block:: cmake

    project(<variant_name>)
    set(CMAKE_CXX_STANDARD 14)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    add_subdirectory(../../../external/gtest ${CMAKE_BINARY_DIR}/gtest_is_here)
    include(GoogleTest)
    include(CTest)
    list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
    enable_testing()

Sets the variant name, configures the C++ standard, integrates the GoogleTest framework, and configures the CTest tool for running the tests with detailed output on failure.

**Component Test Configuration**:

.. code-block:: cmake

    include(${CMAKE_CURRENT_LIST_DIR}/components.cmake)

Includes the ``components.cmake`` file for component-specific test configurations.

components.cmake
----------------
**Component Test Executable and Reporting**:

.. code-block:: cmake

    set(component <component_name>)
    add_executable(${component}_build_test_executable ${component}.c ${component}_test.cc)
    target_link_libraries(${component}_test GTest::gtest_main)
    add_custom_command(
        OUTPUT ${component}_junit.xml
        COMMAND ${CMAKE_CTEST_COMMAND} ${CMAKE_CTEST_ARGUMENTS} --output-junit ${component}_junit.xml || ${CMAKE_COMMAND} -E true
        DEPENDS ${component}_build_test_executable
    )
    add_custom_target(${component}_execute_tests ALL DEPENDS ${component}_junit.xml)
    gtest_discover_tests(${component}_build_test_executable)

Repeats the above block for each component, creating the corresponding test targets.
