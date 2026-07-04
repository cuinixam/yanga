set(CMAKE_C_COMPILER clang CACHE STRING "C Compiler")
set(CMAKE_CXX_COMPILER clang++ CACHE STRING "CXX Compiler")
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

if(APPLE)
    # A standalone LLVM clang does not know the macOS SDK location (Apple clang does).
    # Without it the linker cannot find the system libraries (e.g. _printf).
    if(NOT DEFINED CMAKE_OSX_SYSROOT OR CMAKE_OSX_SYSROOT STREQUAL "")
        execute_process(
            COMMAND xcrun --show-sdk-path
            OUTPUT_VARIABLE _macos_sdk_path
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if(_macos_sdk_path)
            set(CMAKE_OSX_SYSROOT "${_macos_sdk_path}" CACHE PATH "" FORCE)
            message(STATUS "Using macOS SDK: ${_macos_sdk_path}")
        endif()
    endif()
    # The gcc toolchain installed via poks ships its own `ld` which shadows the
    # system linker on PATH. Clang must use the system linker to link against the SDK.
    add_link_options("--ld-path=/usr/bin/ld")
endif()
