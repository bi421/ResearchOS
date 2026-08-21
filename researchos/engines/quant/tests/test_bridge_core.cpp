#include <gtest/gtest.h>
#include "bridge_models.h"
#include <cmath>

using namespace quant::bridge;

namespace {

TEST(BridgeCore, CanonicalFloatFixedTenDecimals) {
  EXPECT_EQ("1.0000000000", canonical_float(1.0));
  EXPECT_EQ("100000.0000000000", canonical_float(100000.0));
  EXPECT_EQ("-0.0000000000", canonical_float(-0.0));
  EXPECT_EQ("0.1000000000", canonical_float(0.1));
  EXPECT_EQ("1.5000000000", canonical_float(1.5));
}

TEST(BridgeCore, CanonicalFloatDeterministic) {
  const double v = 42.123456789;
  EXPECT_EQ(canonical_float(v), canonical_float(v));
}

TEST(BridgeCore, CanonicalEscapeQuotesAndBackslashes) {
  EXPECT_EQ("\\\"", canonical_json_escape("\""));
  EXPECT_EQ("\\\\", canonical_json_escape("\\"));
  EXPECT_EQ("a\\nb", canonical_json_escape("a\nb"));
  EXPECT_EQ("a\\tb", canonical_json_escape("a\tb"));
  EXPECT_EQ("a\\rb", canonical_json_escape("a\rb"));
  EXPECT_EQ("\\u0001", canonical_json_escape(std::string(1, '\x01')));
}

TEST(BridgeCore, CanonicalObjectSortsKeys) {
  auto out = canonical_object({{"zeta", "1"}, {"alpha", "2"}, {"mid", "3"}});
  EXPECT_EQ("{\"alpha\":2,\"mid\":3,\"zeta\":1}", out);
}

TEST(BridgeCore, CanonicalObjectEscapesKeys) {
  auto out = canonical_object({{"a\"b", "1"}});
  EXPECT_EQ("{\"a\\\"b\":1}", out);
}

TEST(BridgeCore, Sha256EmptyVector) {
  EXPECT_EQ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            sha256_hex(""));
}

TEST(BridgeCore, Sha256KnownVectorAbc) {
  EXPECT_EQ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            sha256_hex("abc"));
}

TEST(BridgeCore, Sha256KnownVectorFox) {
  EXPECT_EQ("d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
            sha256_hex("The quick brown fox jumps over the lazy dog"));
}

TEST(BridgeCore, Sha256DeterministicAndLength) {
  const auto a = sha256_hex("researchos-bridge-2026");
  const auto b = sha256_hex("researchos-bridge-2026");
  EXPECT_EQ(a, b);
  EXPECT_EQ(64u, a.size());
  EXPECT_EQ(64u, sha256_hex("x").size());
}

TEST(BridgeCore, CandleCanonicalIsSortedJson) {
  CandleModel c;
  c.timestamp = "2026-01-01T00:00:00";
  c.open = 1.0; c.high = 2.0; c.low = 0.5; c.close = 1.5; c.volume = 10.0;
  c.timeframe = "M1";
  const auto s = c.to_canonical();
  EXPECT_EQ("{\"close\":1.5000000000,\"high\":2.0000000000,"
            "\"low\":0.5000000000,\"open\":1.0000000000,"
            "\"timeframe\":\"M1\",\"timestamp\":\"2026-01-01T00:00:00\","
            "\"volume\":10.0000000000}",
            s);
}

TEST(BridgeCore, CandleCanonicalDeterministic) {
  CandleModel c;
  c.timestamp = "2026-06-15T09:30:00";
  c.open = 3.25; c.high = 3.9; c.low = 3.1; c.close = 3.7; c.volume = 500;
  c.timeframe = "M5";
  EXPECT_EQ(c.to_canonical(), c.to_canonical());
}

TEST(BridgeCore, Iso8601NowFormat) {
  const auto s = iso8601_now();
  ASSERT_EQ(19u, s.size());
  EXPECT_EQ('T', s[10]);
  EXPECT_EQ('-', s[4]);
  EXPECT_EQ('-', s[7]);
  EXPECT_EQ(':', s[13]);
  EXPECT_EQ(':', s[16]);
}

TEST(BridgeCore, CanonicalArraysAndMapsDeterministic) {
  const std::vector<double> vals{1.0, -2.5, 0.0};
  EXPECT_EQ("[1.0000000000,-2.5000000000,0.0000000000]",
            canonical_float_array(vals));
  const std::vector<std::string> strs{"b", "a"};
  EXPECT_EQ("[\"b\",\"a\"]", canonical_string_array(strs));
  const std::unordered_map<std::string, double> m{{"y", 2.0}, {"x", 1.0}};
  EXPECT_EQ("{\"x\":1.0000000000,\"y\":2.0000000000}",
            canonical_double_map(m));
}

} // namespace
