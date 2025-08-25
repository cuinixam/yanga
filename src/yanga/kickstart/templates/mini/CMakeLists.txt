cmake_minimum_required(VERSION 3.20)
include("build/${VARIANT}/${PLATFORM}/config.cmake")
project(MyProject C ASM CXX)
include("${CMAKE_SOURCE_DIR}/build/${VARIANT}/${PLATFORM}/variant.cmake")
