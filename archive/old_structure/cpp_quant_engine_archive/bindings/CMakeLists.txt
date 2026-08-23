# Python bindings for the C++ Quant Engine.
#
# NOTE: this directory is NOT added via add_subdirectory() from the root
# project. The root CMakeLists.txt builds the `cpp_quant_backend` module from
# bindings/python_bindings.cpp when BUILD_PYTHON_BINDINGS=ON. This file exists
# only to document/verify the module target when configured standalone.

if(NOT TARGET quant_engine)
    message(FATAL_ERROR "bindings/ must be configured from the root project")
endif()

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(cpp_quant_backend python_bindings.cpp)
target_link_libraries(cpp_quant_backend PRIVATE quant_engine)
target_include_directories(cpp_quant_backend
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
        ${CMAKE_CURRENT_SOURCE_DIR}/../python
)
target_compile_features(cpp_quant_backend PRIVATE cxx_std_20)
set_target_properties(cpp_quant_backend PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../python/cpp_quant_engine"
)
