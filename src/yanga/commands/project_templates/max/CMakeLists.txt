# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(MyProject)

# Set C standard
set(CMAKE_C_STANDARD 99)

# Set Clang as the compiler
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

# Add your source files here
set(SOURCE_FILES
    src/main.c
)

# Include subdirectories
add_subdirectory(src/sensor)
add_subdirectory(src/low_pass_filter)
add_subdirectory(src/state_machine)

# Create the executable
add_executable(MyProject ${SOURCE_FILES})

# Link the libraries to the executable
target_link_libraries(MyProject sensor low_pass_filter state_machine)
