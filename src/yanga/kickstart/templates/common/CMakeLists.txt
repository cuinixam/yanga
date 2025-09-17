cmake_minimum_required(VERSION 3.20)
include(".yanga/build/${VARIANT}/${PLATFORM}/config.cmake")
project(MyProject C ASM CXX)
include("${CMAKE_SOURCE_DIR}/.yanga/build/${VARIANT}/${PLATFORM}/variant.cmake")
