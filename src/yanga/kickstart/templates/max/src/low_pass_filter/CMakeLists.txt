set(SOURCE_FILES_LOW_PASS_FILTER src/low_pass_filter.c)
add_library(low_pass_filter ${SOURCE_FILES_LOW_PASS_FILTER})
target_include_directories(low_pass_filter PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
