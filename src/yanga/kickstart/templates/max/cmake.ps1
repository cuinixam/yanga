$buildDir = "build/cmake_build"

# Check if build directory exists, if not, create it
if (!(Test-Path -Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir
}

# Navigate into build directory
Set-Location -Path $buildDir

# Run CMake with Ninja generator
cmake -G Ninja ../..

# Build the project with Ninja
ninja

# Navigate back to the root directory
Set-Location -Path ../..
