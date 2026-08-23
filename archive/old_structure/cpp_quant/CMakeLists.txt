cmake_minimum_required(VERSION 3.15)
project(cpp_quant)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Include directories
include_directories(include)

# Core library
set(SOURCES
    src/data_loader.cpp
    src/indicators.cpp
    src/backtest.cpp
    src/statistics.cpp
    src/monte_carlo.cpp
    src/optimizer.cpp
    src/quant_engine.cpp src/audit.cpp
)

add_library(cpp_quant_core SHARED
    ${SOURCES}
    bindings/python_bindings.cpp
)

target_link_libraries(cpp_quant_core
    pybind11::module
    ${Python3_LIBRARIES}
)

# Set output directory
set_target_properties(cpp_quant_core PROPERTIES
    PREFIX ""
    SUFFIX ".pyd"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python/cpp_quant
)

# Tests
option(BUILD_TESTS "Build tests" OFF)
if(BUILD_TESTS)
    find_package(GTest REQUIRED)
    include_directories(${GTEST_INCLUDE_DIRS})
    add_executable(run_tests tests/test_backtest.cpp)
    target_link_libraries(run_tests cpp_quant_core ${GTEST_LIBRARIES} pthread)
endif()

# Version
target_compile_definitions(cpp_quant_core PRIVATE VERSION_INFO=\"1.0.0\")
