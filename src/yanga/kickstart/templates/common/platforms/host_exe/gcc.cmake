set(CMAKE_C_COMPILER gcc CACHE STRING "C Compiler")
set(CMAKE_CXX_COMPILER g++ CACHE STRING "CXX Compiler")
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

if(APPLE)
    # Assemble and link with Apple's `as` and `ld` from the Command Line Tools, not the
    # copies bundled with the portable gcc. A gcc on macOS always depends on Apple's SDK
    # (headers, libSystem, the .tbd stubs), and only Apple's current `ld` reads the stub
    # format the SDK ships with: the bundled ld64-956 rejects the SDK 26.5/27 stubs
    # ("unknown architecture arm64e.x1-macos"), while the bundled `as` already execs
    # clang. Homebrew's gcc works the same way. -B makes the gcc driver look there first.
    set(CMAKE_C_FLAGS_INIT "-B/usr/bin")
    set(CMAKE_CXX_FLAGS_INIT "-B/usr/bin")
    set(CMAKE_EXE_LINKER_FLAGS_INIT "-B/usr/bin")

    # The newest macOS SDK headers use macros (e.g. xnu_static_assert_struct_size)
    # that GCC cannot parse. Fall back to an older compatible SDK if available.
    if(NOT DEFINED CMAKE_OSX_SYSROOT OR CMAKE_OSX_SYSROOT STREQUAL "")
        foreach(_sdk_ver 15.4 15)
            set(_candidate "/Library/Developer/CommandLineTools/SDKs/MacOSX${_sdk_ver}.sdk")
            if(EXISTS "${_candidate}")
                set(CMAKE_OSX_SYSROOT "${_candidate}" CACHE PATH "" FORCE)
                message(STATUS "Using compatible macOS SDK: ${_candidate}")
                break()
            endif()
        endforeach()
    endif()

    find_program(ACTUAL_CXX_COMPILER NAMES ${CMAKE_CXX_COMPILER} g++)
    if(ACTUAL_CXX_COMPILER)
        get_filename_component(COMPILER_BIN_DIR ${ACTUAL_CXX_COMPILER} DIRECTORY)
        get_filename_component(COMPILER_ROOT_DIR ${COMPILER_BIN_DIR} DIRECTORY)
        set(CUSTOM_LIBCXX_DIR "${COMPILER_ROOT_DIR}/lib")
        if(EXISTS "${CUSTOM_LIBCXX_DIR}/libc++.1.dylib")
            # Ensure the linker picks up the correct libc++ (not the system one) and
            # that the @rpath/libc++.1.dylib install name resolves at runtime.
            add_link_options("-L${CUSTOM_LIBCXX_DIR}" "-Wl,-rpath,${CUSTOM_LIBCXX_DIR}")
            message(STATUS "Using libc++: ${CUSTOM_LIBCXX_DIR}")
        else()
            message(WARNING "libc++.1.dylib not found at ${CUSTOM_LIBCXX_DIR}")
        endif()
    endif()
endif()
