include(FetchContent)
# Build googletest as static libs (avoids DLL PATH issues when running tests).
set(BUILD_SHARED_LIBS OFF)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.15.2
)
FetchContent_MakeAvailable(googletest)

file(GLOB TEST_SOURCES CONFIGURE_DEPENDS *.cpp)
# test_statistics.cpp is a legacy self-contained harness (own main(), tests the
# deprecated `quant_engine` namespace). It conflicts with gtest_discover_tests,
# so it is excluded from the GoogleTest suite.
list(FILTER TEST_SOURCES EXCLUDE REGEX "test_statistics\\.cpp$")
add_executable(quant_engine_tests ${TEST_SOURCES})
target_link_libraries(quant_engine_tests PRIVATE quant_engine GTest::gtest_main)
target_include_directories(quant_engine_tests PRIVATE ${gtest_SOURCE_DIR}/include)

include(GoogleTest)
gtest_discover_tests(quant_engine_tests)
