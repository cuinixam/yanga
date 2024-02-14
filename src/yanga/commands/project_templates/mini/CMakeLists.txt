cmake_minimum_required(VERSION 3.20)
project(MyProject)

if (${BUILD_KIT} STREQUAL "test")
    include(${CMAKE_SOURCE_DIR}/build/${VARIANT}/build/test/variant.cmake)
else()
    include(${CMAKE_SOURCE_DIR}/build/${VARIANT}/build/variant.cmake)
endif()
