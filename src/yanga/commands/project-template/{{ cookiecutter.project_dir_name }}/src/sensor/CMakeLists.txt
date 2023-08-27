set(SOURCE_FILES_SENSOR src/sensor.c)
add_library(sensor ${SOURCE_FILES_SENSOR})
target_include_directories(sensor PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
