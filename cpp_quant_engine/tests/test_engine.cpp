#include <gtest/gtest.h>
#include "quant/core/engine.h"

using namespace quant;

TEST(EngineTest, Version) {
  auto v = QuantEngine::version();
  EXPECT_GE(v.major, 0);
  EXPECT_EQ(1, v.minor);
  EXPECT_EQ(0, v.patch);
}

TEST(EngineTest, About) {
  auto about = QuantEngine::about();
  EXPECT_TRUE(about.find("QuantEngine") != std::string::npos);
}

TEST(EngineTest, Initialize) {
  QuantEngine engine;
  Config cfg = Config::object();
  cfg.set("mode", Config(std::string("test")));
  auto r = engine.initialize(cfg);
  EXPECT_TRUE(r.is_ok());
  EXPECT_TRUE(engine.is_initialized());
}

TEST(EngineTest, DoubleInitFails) {
  QuantEngine engine;
  Config cfg;
  engine.initialize(cfg);
  auto r = engine.initialize(cfg);
  EXPECT_TRUE(r.is_err());
}

TEST(EngineTest, Shutdown) {
  QuantEngine engine;
  Config cfg;
  engine.initialize(cfg);
  EXPECT_TRUE(engine.is_initialized());
  engine.shutdown();
  EXPECT_FALSE(engine.is_initialized());
}

TEST(EngineTest, ConfigAccess) {
  QuantEngine engine;
  Config cfg = Config::object();
  cfg.set("key", Config(42));
  engine.initialize(cfg);
  EXPECT_EQ(42, engine.config()["key"].get_int().value());
}

TEST(EngineTest, ConfigNotFound) {
  QuantEngine engine;
  engine.initialize(Config::object());
  auto r = engine.config().get("nonexistent");
  EXPECT_TRUE(r.is_err());
}
