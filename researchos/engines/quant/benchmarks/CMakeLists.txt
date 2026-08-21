file(GLOB BENCH_SOURCES CONFIGURE_DEPENDS *.cpp)
add_executable(quant_engine_bench ${BENCH_SOURCES})
target_link_libraries(quant_engine_bench PRIVATE quant_engine)
target_include_directories(quant_engine_bench PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include)
