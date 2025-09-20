set(CMAKE_C_COMPILER clang CACHE STRING "C Compiler")
set(CMAKE_CXX_COMPILER clang++ CACHE STRING "CXX Compiler")
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

if(DEFINED LINKER_SCRIPT)
    set(linker_script_path "${PROJECT_SOURCE_DIR}/${LINKER_SCRIPT}")
    if(NOT EXISTS "${linker_script_path}")
        message(WARNING "Linker script not found: ${linker_script_path}")
    else()
        message(STATUS "Using custom linker script: ${linker_script_path}")
        # Use LINKER: prefix to ensure this is only passed to the linker, not compiler
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-T${linker_script_path}")
    endif()

endif()
