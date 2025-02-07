set(SOURCE_FILES_STATE_MACHINE src/state_machine.c)
add_library(state_machine ${SOURCE_FILES_STATE_MACHINE})
target_include_directories(state_machine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
