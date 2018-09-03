cmake_minimum_required(VERSION 3.9.0)
project(riks)

add_definitions(-DHYKER_API_EXPORTS)

if ($<CXX_COMPILER_ID:GNU>)
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--no-undefined")
endif ()

add_compile_options(
    "$<$<CXX_COMPILER_ID:GNU>:-Os>"
    "$<$<CXX_COMPILER_ID:GNU>:-s>"
    "$<$<CXX_COMPILER_ID:GNU>:-Wall>"
    "$<$<CXX_COMPILER_ID:GNU>:-Wextra>"
    "$<$<AND:$<CXX_COMPILER_ID:GNU>,$<CONFIG:DEBUG>>:-g3>"
    "$<$<AND:$<CXX_COMPILER_ID:GNU>,$<CONFIG:DEBUG>>:-fno-omit-frame-pointer>"

    "$<$<CXX_COMPILER_ID:Clang>:-Os>"
    "$<$<CXX_COMPILER_ID:Clang>:-Wall>"
    "$<$<CXX_COMPILER_ID:Clang>:-Wextra>"
    "$<$<AND:$<CXX_COMPILER_ID:Clang>,$<CONFIG:DEBUG>>:-g3>"
    "$<$<AND:$<CXX_COMPILER_ID:Clang>,$<CONFIG:DEBUG>>:-fno-omit-frame-pointer>"

    "$<$<CXX_COMPILER_ID:AppleClang>:-fembed-bitcode>"

    "$<$<AND:$<CXX_COMPILER_ID:MSVC>,$<CONFIG:DEBUG>>:/Od>"
    "$<$<AND:$<CXX_COMPILER_ID:MSVC>,$<CONFIG:RELEASE>>:/Os>"
)

set(MACOSX_RPATH                    OFF)
set(THREADS_PREFER_PTHREAD_FLAG     ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_BUILD_RPATH               "$ORIGIN")
set(CMAKE_CXX_STANDARD              17)
set(CMAKE_CXX_STANDARD_REQUIRE      ON)
set(CMAKE_CXX_EXTENSIONS            OFF)

option(BUILD_TESTS "Build tests" ON)

# Conan
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

# RIKS++

add_library(${PROJECT_NAME}-object OBJECT "")
add_library(${PROJECT_NAME}-shared SHARED "")
add_library(${PROJECT_NAME}-static STATIC "")
add_library(${PROJECT_NAME}-interface INTERFACE)

set(${PROJECT_NAME}_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_sources(${PROJECT_NAME}-object
    PUBLIC
        ${${PROJECT_NAME}_SOURCE_DIR}/donalonzo/hello_world.cpp)

target_include_directories(${PROJECT_NAME}-object PUBLIC ${${PROJECT_NAME}_SOURCE_DIR})
target_include_directories(${PROJECT_NAME}-interface INTERFACE ${${PROJECT_NAME}_SOURCE_DIR})

set_target_properties(${PROJECT_NAME}-interface PROPERTIES INTERFACE_SOURCES $<TARGET_OBJECTS:${PROJECT_NAME}-object>)
set_target_properties(${PROJECT_NAME}-shared PROPERTIES OUTPUT_NAME ${PROJECT_NAME})
set_target_properties(${PROJECT_NAME}-static PROPERTIES OUTPUT_NAME ${PROJECT_NAME}-static)

# Dependencies

find_package(Threads REQUIRED)

target_link_libraries(${PROJECT_NAME}-interface
    INTERFACE
        ${CONAN_LIBS})

target_link_libraries(${PROJECT_NAME}-shared PUBLIC ${PROJECT_NAME}-interface)
target_link_libraries(${PROJECT_NAME}-static PUBLIC ${PROJECT_NAME}-interface)

# Tests

if (BUILD_TESTS)
    add_executable(${PROJECT_NAME}-tests
        tests/hello_world.cpp
        tests/main.cpp)

    target_link_libraries(${PROJECT_NAME}-tests PRIVATE ${PROJECT_NAME}-interface)

    enable_testing()
    if (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
        add_test(${PROJECT_NAME}-tests bin/${PROJECT_NAME}-tests -r compact --use-colour yes --invisibles)
    else (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
        add_test(NAME    ${PROJECT_NAME}-tests
                 COMMAND ${PROJECT_NAME}-tests -r compact --use-colour yes --invisibles)
    endif ()
endif (BUILD_TESTS)
