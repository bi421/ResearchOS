#include <gtest/gtest.h>
#include "quant/core/error.h"
#include "quant/core/result.h"
#include "quant/core/logger.h"
#include "quant/core/config.h"
#include <string>

using namespace quant;

TEST(ErrorTest, DefaultConstruct) {
  Error e;
  EXPECT_FALSE(e);
  EXPECT_EQ(ErrorCode::None, e.code());
}

TEST(ErrorTest, CreateWithCode) {
  Error e(ErrorCode::InvalidArgument, "bad arg");
  EXPECT_TRUE(e);
  EXPECT_EQ(ErrorCode::InvalidArgument, e.code());
  EXPECT_EQ("bad arg", e.message());
}

TEST(ErrorTest, WhatContainsInfo) {
  Error e(ErrorCode::DivisionByZero, "divide by zero");
  auto w = e.what();
  EXPECT_TRUE(w.find("divide by zero") != std::string::npos);
}

TEST(ResultTest, OkValue) {
  auto r = Result<int>::ok(42);
  EXPECT_TRUE(r.is_ok());
  EXPECT_FALSE(r.is_err());
  EXPECT_TRUE(r);
  EXPECT_EQ(42, r.value());
}

TEST(ResultTest, ErrValue) {
  auto r = Result<int>::fail(Error(ErrorCode::InvalidArgument, "bad"));
  EXPECT_FALSE(r.is_ok());
  EXPECT_TRUE(r.is_err());
  EXPECT_FALSE(r);
  EXPECT_EQ(ErrorCode::InvalidArgument, r.error().code());
}

TEST(ResultTest, MapSuccess) {
  auto r = Result<int>::ok(10).map([](int x) { return x * 2.0; });
  EXPECT_TRUE(r.is_ok());
  EXPECT_DOUBLE_EQ(20.0, r.value());
}

TEST(ResultTest, MapOnErr) {
  auto r = Result<int>(Error(ErrorCode::RuntimeError, "fail"));
  auto r2 = r.map([](int) { return 0; });
  EXPECT_TRUE(r2.is_err());
}

TEST(ResultTest, AndThenSuccess) {
  auto r = Result<int>::ok(5).and_then([](int x) {
    return Result<int>::ok(x + 3);
  });
  EXPECT_TRUE(r.is_ok());
  EXPECT_EQ(8, r.value());
}

TEST(ResultTest, AndThenFailure) {
  auto r = Result<int>::ok(5).and_then([](int) {
    return Result<int>::fail(Error(ErrorCode::RuntimeError, "fail"));
  });
  EXPECT_TRUE(r.is_err());
}

TEST(ResultTest, ValueOr) {
  Result<int> ok_r(42);
  EXPECT_EQ(42, ok_r.value_or(-1));
  Result<int> err_r(Error(ErrorCode::RuntimeError, "err"));
  EXPECT_EQ(-1, err_r.value_or(-1));
}

TEST(ResultTest, VoidOk) {
  auto r = Result<void>::ok();
  EXPECT_TRUE(r.is_ok());
  EXPECT_TRUE(r);
}

TEST(ResultTest, VoidFail) {
  auto r = Result<void>::fail(Error(ErrorCode::RuntimeError, "fail"));
  EXPECT_TRUE(r.is_err());
  EXPECT_FALSE(r);
}

TEST(LoggerTest, Singleton) {
  auto& l1 = Logger::instance();
  auto& l2 = Logger::instance();
  EXPECT_EQ(&l1, &l2);
}

TEST(LoggerTest, LogAndRetrieve) {
  Logger::instance().clear();
  Logger::instance().set_level(LogLevel::Trace);
  auto log_msg = std::format("hello {}", 42);
  Logger::instance().info(log_msg);
  EXPECT_EQ(1, Logger::instance().entries().size());
  EXPECT_EQ("hello 42", Logger::instance().entries()[0].message);
}

TEST(LoggerTest, LevelFiltering) {
  Logger::instance().clear();
  Logger::instance().set_level(LogLevel::Warn);
  Logger::instance().debug("should not appear");
  EXPECT_EQ(0, Logger::instance().entries().size());
  Logger::instance().warn("should appear");
  EXPECT_EQ(1, Logger::instance().entries().size());
}

TEST(ConfigTest, NullDefault) {
  Config c;
  EXPECT_TRUE(c.is_null());
}

TEST(ConfigTest, BoolValue) {
  Config c(true);
  EXPECT_TRUE(c.is_bool());
  EXPECT_TRUE(c.get_bool().value());
}

TEST(ConfigTest, IntValue) {
  Config c(int64_t(123));
  EXPECT_TRUE(c.is_int());
  EXPECT_EQ(123, c.get_int().value());
}

TEST(ConfigTest, DoubleValue) {
  Config c(3.14);
  EXPECT_TRUE(c.is_double());
  EXPECT_DOUBLE_EQ(3.14, c.get_double().value());
}

TEST(ConfigTest, StringValue) {
  Config c(std::string("hello"));
  EXPECT_TRUE(c.is_string());
  EXPECT_EQ("hello", c.get_string().value());
}

TEST(ConfigTest, ObjectAccess) {
  Config obj = Config::object();
  obj.set("key", Config(42));
  EXPECT_TRUE(obj.is_object());
  EXPECT_TRUE(obj.has("key"));
  EXPECT_EQ(42, obj["key"].get_int().value());
}

TEST(ConfigTest, ArrayAccess) {
  Config arr = Config::array();
  arr.push_back(Config(1));
  arr.push_back(Config(2));
  EXPECT_TRUE(arr.is_array());
  auto a = arr.get_array().value();
  EXPECT_EQ(2, a.size());
  EXPECT_EQ(1, a[0].get_int().value());
}

TEST(ConfigTest, NestedPath) {
  Config obj = Config::object();
  obj["a"]["b"] = Config(42);
  auto r = obj.get("a.b");
  EXPECT_TRUE(r.is_ok());
  EXPECT_EQ(42, r.value().get_int().value());
}

TEST(ConfigTest, MissingPath) {
  Config obj = Config::object();
  auto r = obj.get("missing.key");
  EXPECT_TRUE(r.is_err());
}

TEST(ConfigTest, ToStringJson) {
  Config obj = Config::object();
  obj.set("name", Config(std::string("test")));
  obj.set("value", Config(int64_t(99)));
  auto s = obj.to_string();
  EXPECT_TRUE(s.find("test") != std::string::npos);
  EXPECT_TRUE(s.find("99") != std::string::npos);
}

TEST(ConfigTest, ParseJsonObject) {
  auto c = Config::parse_json(R"({"a":1,"b":"hello"})");
  EXPECT_TRUE(c.is_object());
  EXPECT_EQ(1, c["a"].get_int().value());
  EXPECT_EQ("hello", c["b"].get_string().value());
}

TEST(ConfigTest, ParseJsonArray) {
  auto c = Config::parse_json("[1,2,3]");
  EXPECT_TRUE(c.is_array());
  auto arr = c.get_array().value();
  EXPECT_EQ(3, arr.size());
}

TEST(ConfigTest, ParseJsonNested) {
  auto c = Config::parse_json(R"({"outer":{"inner":42}})");
  EXPECT_EQ(42, c["outer"]["inner"].get_int().value());
}

TEST(ConfigTest, ParseJsonNumbers) {
  auto c = Config::parse_json(R"({"i":42,"f":3.14})");
  EXPECT_EQ(42, c["i"].get_int().value());
  EXPECT_DOUBLE_EQ(3.14, c["f"].get_double().value());
}
