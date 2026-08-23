#include "quant/backtest/serialization.h"
#include <algorithm>
#include <charconv>
#include <chrono>
#include <cstdio>
#include <format>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>

namespace quant {
namespace serialization {

namespace {

// ── General number formatting / parsing ────────────────────────────────────

std::string to_general(double v) {
  char buf[64];
  auto res = std::to_chars(buf, buf + sizeof(buf), v, std::chars_format::general);
  if (res.ec == std::errc{}) return std::string(buf, res.ptr);
  return std::to_string(v);
}

bool parse_double(std::string_view sv, double& out) {
  if (sv.empty()) return false;
  const char* begin = sv.data();
  const char* end = begin + sv.size();
  auto res = std::from_chars(begin, end, out, std::chars_format::general);
  return res.ec == std::errc{} && res.ptr == end;
}

std::optional<uint64_t> parse_u64(std::string_view sv) {
  uint64_t v = 0;
  const char* begin = sv.data();
  const char* end = begin + sv.size();
  auto res = std::from_chars(begin, end, v);
  if (res.ec == std::errc{} && res.ptr == end) return v;
  return std::nullopt;
}

// ── Timeframe helpers ──────────────────────────────────────────────────────

Timeframe timeframe_from_name(std::string_view name) {
  if (name == "M1") return Timeframe::M1;
  if (name == "M5") return Timeframe::M5;
  if (name == "M15") return Timeframe::M15;
  if (name == "M30") return Timeframe::M30;
  if (name == "H1") return Timeframe::H1;
  if (name == "H4") return Timeframe::H4;
  if (name == "D1") return Timeframe::D1;
  if (name == "W1") return Timeframe::W1;
  if (name == "MN1") return Timeframe::MN1;
  return Timeframe::M1;
}

// ── Minimal JSON support ───────────────────────────────────────────────────

struct JsonValue {
  enum class Kind { Null, Bool, Number, String, Array, Object };
  Kind kind{Kind::Null};
  bool boolean{false};
  double number{0.0};
  std::string string;
  std::vector<JsonValue> array;
  std::vector<std::pair<std::string, JsonValue>> object;

  const JsonValue* find(const std::string& key) const {
    if (kind != Kind::Object) return nullptr;
    for (const auto& [k, v] : object)
      if (k == key) return &v;
    return nullptr;
  }
};

std::string json_escape(std::string_view s) {
  std::string out;
  out.reserve(s.size() + 2);
  for (char c : s) {
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\t': out += "\\t"; break;
      case '\r': out += "\\r"; break;
      case '\b': out += "\\b"; break;
      case '\f': out += "\\f"; break;
      default:
        if (static_cast<unsigned char>(c) < 0x20) {
          char buf[7];
          std::snprintf(buf, sizeof(buf), "\\u%04x", c);
          out += buf;
        } else {
          out += c;
        }
    }
  }
  return out;
}

struct JsonParser {
  std::string_view src;
  size_t pos{0};
  std::string error;

  bool eof() const { return pos >= src.size(); }
  char peek() const { return eof() ? '\0' : src[pos]; }
  char next() { return eof() ? '\0' : src[pos++]; }
  void skip_ws() {
    while (!eof()) {
      const char c = src[pos];
      if (c == ' ' || c == '\t' || c == '\n' || c == '\r') ++pos;
      else break;
    }
  }
  bool expect(char c) {
    skip_ws();
    if (!eof() && src[pos] == c) { ++pos; return true; }
    return false;
  }
  bool literal(std::string_view lit) {
    skip_ws();
    if (src.substr(pos, lit.size()) == lit) { pos += lit.size(); return true; }
    return false;
  }
};

std::optional<JsonValue> parse_value(JsonParser& p);

std::optional<JsonValue> parse_string(JsonParser& p) {
  if (!p.expect('"')) { p.error = "expected string"; return std::nullopt; }
  std::string out;
  while (!p.eof()) {
    char c = p.next();
    if (c == '"') { JsonValue v; v.kind = JsonValue::Kind::String; v.string = std::move(out); return v; }
    if (c == '\\') {
      if (p.eof()) { p.error = "unterminated escape"; return std::nullopt; }
      char e = p.next();
      switch (e) {
        case '"': out += '"'; break;
        case '\\': out += '\\'; break;
        case '/': out += '/'; break;
        case 'n': out += '\n'; break;
        case 't': out += '\t'; break;
        case 'r': out += '\r'; break;
        case 'b': out += '\b'; break;
        case 'f': out += '\f'; break;
        default: out += e; break;
      }
    } else {
      out += c;
    }
  }
  p.error = "unterminated string";
  return std::nullopt;
}

std::optional<JsonValue> parse_number(JsonParser& p) {
  p.skip_ws();
  const size_t start = p.pos;
  while (!p.eof()) {
    const char c = p.src[p.pos];
    if ((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' ||
        c == 'e' || c == 'E') {
      ++p.pos;
    } else {
      break;
    }
  }
  double d = 0.0;
  if (!parse_double(p.src.substr(start, p.pos - start), d)) {
    p.error = "invalid number";
    return std::nullopt;
  }
  JsonValue v;
  v.kind = JsonValue::Kind::Number;
  v.number = d;
  return v;
}

std::optional<JsonValue> parse_array(JsonParser& p) {
  if (!p.expect('[')) { p.error = "expected array"; return std::nullopt; }
  JsonValue v;
  v.kind = JsonValue::Kind::Array;
  p.skip_ws();
  if (p.peek() == ']') { ++p.pos; return v; }
  while (true) {
    auto item = parse_value(p);
    if (!item) return std::nullopt;
    v.array.push_back(std::move(*item));
    p.skip_ws();
    if (p.eof()) { p.error = "unterminated array"; return std::nullopt; }
    if (p.peek() == ',') { ++p.pos; continue; }
    if (p.peek() == ']') { ++p.pos; return v; }
    p.error = "expected , or ]";
    return std::nullopt;
  }
}

std::optional<JsonValue> parse_object(JsonParser& p) {
  if (!p.expect('{')) { p.error = "expected object"; return std::nullopt; }
  JsonValue v;
  v.kind = JsonValue::Kind::Object;
  p.skip_ws();
  if (p.peek() == '}') { ++p.pos; return v; }
  while (true) {
    auto key = parse_string(p);
    if (!key) return std::nullopt;
    if (!p.expect(':')) { p.error = "expected :"; return std::nullopt; }
    auto val = parse_value(p);
    if (!val) return std::nullopt;
    v.object.emplace_back(key->string, std::move(*val));
    p.skip_ws();
    if (p.eof()) { p.error = "unterminated object"; return std::nullopt; }
    if (p.peek() == ',') { ++p.pos; continue; }
    if (p.peek() == '}') { ++p.pos; return v; }
    p.error = "expected , or }";
    return std::nullopt;
  }
}

std::optional<JsonValue> parse_value(JsonParser& p) {
  p.skip_ws();
  if (p.eof()) { p.error = "unexpected end"; return std::nullopt; }
  switch (p.peek()) {
    case '{': return parse_object(p);
    case '[': return parse_array(p);
    case '"': return parse_string(p);
    case 't':
      if (p.literal("true")) {
        JsonValue v; v.kind = JsonValue::Kind::Bool; v.boolean = true; return v;
      }
      p.error = "bad literal"; return std::nullopt;
    case 'f':
      if (p.literal("false")) {
        JsonValue v; v.kind = JsonValue::Kind::Bool; v.boolean = false; return v;
      }
      p.error = "bad literal"; return std::nullopt;
    case 'n':
      if (p.literal("null")) {
        JsonValue v; v.kind = JsonValue::Kind::Null; return v;
      }
      p.error = "bad literal"; return std::nullopt;
    default: return parse_number(p);
  }
}

std::optional<JsonValue> parse_json(std::string_view src, std::string& error) {
  JsonParser p{src, 0, {}};
  auto v = parse_value(p);
  if (!v) { error = p.error.empty() ? "parse error" : p.error; return std::nullopt; }
  p.skip_ws();
  if (!p.eof()) { error = "trailing characters"; return std::nullopt; }
  return v;
}

// ── CSV helpers ────────────────────────────────────────────────────────────

std::vector<std::string_view> split_line(std::string_view line, char delim) {
  std::vector<std::string_view> parts;
  size_t start = 0;
  for (size_t i = 0; i <= line.size(); ++i) {
    if (i == line.size() || line[i] == delim) {
      parts.push_back(line.substr(start, i - start));
      start = i + 1;
    }
  }
  return parts;
}

} // namespace

// ── Timestamps ─────────────────────────────────────────────────────────────

std::string to_iso8601(TimePoint tp) {
  const auto days = std::chrono::floor<std::chrono::days>(tp);
  const std::chrono::year_month_day ymd{days};
  const std::chrono::hh_mm_ss tod{tp - days};
  return std::format(
      "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}",
      static_cast<int>(ymd.year()), static_cast<unsigned>(ymd.month()),
      static_cast<unsigned>(ymd.day()), tod.hours().count(),
      tod.minutes().count(), static_cast<int64_t>(tod.seconds().count()));
}

TimePoint from_iso8601(std::string_view str) {
  // Expected: YYYY-MM-DDTHH:MM:SS (optionally followed by .fraction/Z/offset).
  int y = 0, mo = 0, d = 0, h = 0, mi = 0, se = 0;
  if (str.size() < 19) return TimePoint{};
  const auto read = [&](size_t off, int len) -> int {
    int v = 0;
    for (int k = 0; k < len; ++k) {
      const char c = str[off + static_cast<size_t>(k)];
      if (c < '0' || c > '9') return -1;
      v = v * 10 + (c - '0');
    }
    return v;
  };
  y = read(0, 4); mo = read(5, 2); d = read(8, 2);
  h = read(11, 2); mi = read(14, 2); se = read(17, 2);
  if (y < 0 || mo < 0 || d < 0 || h < 0 || mi < 0 || se < 0) return TimePoint{};
  if (str[4] != '-' || str[7] != '-' || str[10] != 'T' || str[13] != ':' || str[16] != ':')
    return TimePoint{};

  return std::chrono::sys_days{
             std::chrono::year{y} / std::chrono::month{static_cast<unsigned>(mo)} /
             std::chrono::day{static_cast<unsigned>(d)}} +
         std::chrono::hours{h} + std::chrono::minutes{mi} + std::chrono::seconds{se};
}

// ── Candle CSV ─────────────────────────────────────────────────────────────

Result<std::string> candles_to_csv(const std::vector<Candle>& candles) {
  std::string out;
  out.reserve(candles.size() * 96);
  out += "timestamp,open,high,low,close,volume,trade_count,vwap,timeframe\n";
  for (const auto& c : candles) {
    out += to_iso8601(c.timestamp);
    out += ',';
    out += to_general(c.open);
    out += ',';
    out += to_general(c.high);
    out += ',';
    out += to_general(c.low);
    out += ',';
    out += to_general(c.close);
    out += ',';
    out += to_general(c.volume);
    out += ',';
    out += std::to_string(c.trade_count);
    out += ',';
    out += to_general(c.vwap);
    out += ',';
    out += timeframe_name(c.timeframe);
    out += '\n';
  }
  return Result<std::string>::ok(std::move(out));
}

Result<std::vector<Candle>> candles_from_csv(std::string_view csv) {
  std::vector<Candle> out;
  size_t line_start = 0;
  size_t line_no = 0;
  auto finish = [&](size_t end, bool eof) {
    std::string_view line = csv.substr(line_start, end - line_start);
    line_start = end + 1;
    ++line_no;
    // Trim trailing '\r'.
    if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
    if (line.empty()) return true;
    // Skip header row.
    if (line_no == 1 && line.find("timestamp") == 0) return true;
    if (eof && line.empty()) return true;

    auto parts = split_line(line, ',');
    if (parts.size() < 6) {
      out.clear();
      return false;
    }
    auto looks_like_timestamp = [](std::string_view s) {
      if (s.size() < 19) return false;
      return s[4] == '-' && s[7] == '-' && s[10] == 'T' &&
             s[13] == ':' && s[16] == ':';
    };
    if (!looks_like_timestamp(parts[0])) {
      out.clear();
      return false;
    }
    Candle c;
    c.timestamp = from_iso8601(parts[0]);
    if (!parse_double(parts[1], c.open) || !parse_double(parts[2], c.high) ||
        !parse_double(parts[3], c.low) || !parse_double(parts[4], c.close) ||
        !parse_double(parts[5], c.volume)) {
      out.clear();
      return false;
    }
    if (parts.size() >= 7) {
      if (auto tc = parse_u64(parts[6])) c.trade_count = *tc;
    }
    if (parts.size() >= 8) parse_double(parts[7], c.vwap);
    if (parts.size() >= 9) c.timeframe = timeframe_from_name(parts[8]);
    if (!c.is_valid()) {
      out.clear();
      return false;
    }
    out.push_back(c);
    return true;
  };

  bool ok = true;
  while (line_start <= csv.size()) {
    size_t nl = csv.find('\n', line_start);
    bool eof = nl == std::string_view::npos;
    size_t end = eof ? csv.size() : nl;
    if (!finish(end, eof)) { ok = false; break; }
    if (eof) break;
    line_start = end + 1;
  }
  if (!ok) {
    return Result<std::vector<Candle>>::fail(
        Error(ErrorCode::InvalidArgument,
              "serialization::candles_from_csv: malformed CSV at line " +
                  std::to_string(line_no)));
  }
  return Result<std::vector<Candle>>::ok(std::move(out));
}

// ── Event JSON ─────────────────────────────────────────────────────────────

Result<std::string> events_to_json(const std::vector<ReplayEvent>& events) {
  std::string out;
  out.reserve(events.size() * 160);
  out += '[';
  for (size_t i = 0; i < events.size(); ++i) {
    const auto& e = events[i];
    if (i) out += ',';
    out += "{\"seq\":";
    out += std::to_string(e.sequence);
    out += ",\"type\":\"";
    out += event_type_name(e.type);
    out += "\",\"time\":\"";
    out += to_iso8601(e.timestamp);
    out += "\",\"bar\":";
    out += std::to_string(e.bar_index);
    if (e.type == EventType::Candle) {
      out += ",\"candle\":{\"open\":";
      out += to_general(e.candle.open);
      out += ",\"high\":";
      out += to_general(e.candle.high);
      out += ",\"low\":";
      out += to_general(e.candle.low);
      out += ",\"close\":";
      out += to_general(e.candle.close);
      out += ",\"volume\":";
      out += to_general(e.candle.volume);
      out += ",\"timeframe\":\"";
      out += timeframe_name(e.candle.timeframe);
      out += "\"}";
    }
    if (e.type == EventType::Session) {
      out += ",\"status\":\"";
      out += (e.session_status == SessionStatus::Open) ? "open" : "close";
      out += '"';
    }
    out += '}';
  }
  out += ']';
  return Result<std::string>::ok(std::move(out));
}

Result<std::vector<ReplayEvent>> events_from_json(std::string_view json) {
  std::string error;
  auto root = parse_json(json, error);
  if (!root) {
    return Result<std::vector<ReplayEvent>>::fail(
        Error(ErrorCode::InvalidArgument,
              "serialization::events_from_json: " + error));
  }
  if (root->kind != JsonValue::Kind::Array) {
    return Result<std::vector<ReplayEvent>>::fail(
        Error(ErrorCode::InvalidArgument,
              "serialization::events_from_json: expected JSON array"));
  }
  std::vector<ReplayEvent> out;
  out.reserve(root->array.size());
  for (const auto& item : root->array) {
    ReplayEvent e;
    if (auto seq = item.find("seq")) {
      if (seq->kind == JsonValue::Kind::Number) e.sequence = static_cast<uint64_t>(seq->number);
    }
    const auto* type = item.find("type");
    if (!type || type->kind != JsonValue::Kind::String) {
      return Result<std::vector<ReplayEvent>>::fail(
          Error(ErrorCode::InvalidArgument, "serialization::events_from_json: missing type"));
    }
    const std::string& tn = type->string;
    if (tn == "candle") e.type = EventType::Candle;
    else if (tn == "timestamp") e.type = EventType::Timestamp;
    else if (tn == "session") e.type = EventType::Session;
    else {
      return Result<std::vector<ReplayEvent>>::fail(
          Error(ErrorCode::InvalidArgument, "serialization::events_from_json: unknown type '" + tn + "'"));
    }
    if (auto t = item.find("time")) {
      if (t->kind == JsonValue::Kind::String) e.timestamp = from_iso8601(t->string);
    }
    if (auto b = item.find("bar")) {
      if (b->kind == JsonValue::Kind::Number) e.bar_index = static_cast<size_t>(b->number);
    }
    if (e.type == EventType::Candle) {
      if (const auto* cobj = item.find("candle")) {
        auto num = [&](const char* k, double& dst) {
          const auto* v = cobj->find(k);
          if (v && v->kind == JsonValue::Kind::Number) dst = v->number;
        };
        num("open", e.candle.open);
        num("high", e.candle.high);
        num("low", e.candle.low);
        num("close", e.candle.close);
        num("volume", e.candle.volume);
        if (const auto* tf = cobj->find("timeframe")) {
          if (tf->kind == JsonValue::Kind::String) e.candle.timeframe = timeframe_from_name(tf->string);
        }
      }
    }
    if (e.type == EventType::Session) {
      if (const auto* st = item.find("status")) {
        if (st->kind == JsonValue::Kind::String && st->string == "close") {
          e.session_status = SessionStatus::Close;
        }
      }
    }
    out.push_back(e);
  }
  return Result<std::vector<ReplayEvent>>::ok(std::move(out));
}

// ── Report JSON ────────────────────────────────────────────────────────────

namespace {

void append_key(std::string& out, const char* key, double value, bool& first) {
  if (!first) out += ',';
  first = false;
  out += '"';
  out += key;
  out += "\":";
  out += to_general(value);
}

void append_key(std::string& out, const char* key, size_t value, bool& first) {
  if (!first) out += ',';
  first = false;
  out += '"';
  out += key;
  out += "\":";
  out += std::to_string(value);
}

} // namespace

Result<std::string> report_to_json(const PerformanceReport& r) {
  std::string out = "{";
  bool first = true;
  append_key(out, "total_return", r.total_return, first);
  append_key(out, "total_return_pct", r.total_return_pct, first);
  append_key(out, "annualized_return", r.annualized_return, first);
  append_key(out, "annualized_volatility", r.annualized_volatility, first);
  append_key(out, "sharpe_ratio", r.sharpe_ratio, first);
  append_key(out, "sortino_ratio", r.sortino_ratio, first);
  append_key(out, "calmar_ratio", r.calmar_ratio, first);
  append_key(out, "max_drawdown_pct", r.max_drawdown_pct, first);
  append_key(out, "max_drawdown_duration", r.max_drawdown_duration, first);
  append_key(out, "win_rate", r.win_rate, first);
  append_key(out, "profit_factor", r.profit_factor, first);
  append_key(out, "avg_win", r.avg_win, first);
  append_key(out, "avg_loss", r.avg_loss, first);
  append_key(out, "largest_win", r.largest_win, first);
  append_key(out, "largest_loss", r.largest_loss, first);
  append_key(out, "total_trades", r.total_trades, first);
  append_key(out, "winning_trades", r.winning_trades, first);
  append_key(out, "losing_trades", r.losing_trades, first);
  append_key(out, "downside_deviation", r.downside_deviation, first);
  append_key(out, "downside_deviation_annualized", r.downside_deviation_annualized, first);
  append_key(out, "var_95", r.var_95, first);
  append_key(out, "var_99", r.var_99, first);
  append_key(out, "cvar_95", r.cvar_95, first);
  append_key(out, "cvar_99", r.cvar_99, first);
  append_key(out, "max_drawdown_recovery_bars", r.max_drawdown_recovery_bars, first);
  append_key(out, "time_in_drawdown_pct", r.time_in_drawdown_pct, first);
  out += '}';
  return Result<std::string>::ok(std::move(out));
}

Result<std::string> report_to_json(const DetailedPerformanceReport& rep) {
  std::string out = "{";
  bool first = true;
  append_key(out, "total_return", rep.base.total_return, first);
  append_key(out, "total_return_pct", rep.base.total_return_pct, first);
  append_key(out, "annualized_return", rep.base.annualized_return, first);
  append_key(out, "annualized_volatility", rep.base.annualized_volatility, first);
  append_key(out, "sharpe_ratio", rep.base.sharpe_ratio, first);
  append_key(out, "sortino_ratio", rep.base.sortino_ratio, first);
  append_key(out, "calmar_ratio", rep.base.calmar_ratio, first);
  append_key(out, "max_drawdown_pct", rep.base.max_drawdown_pct, first);
  append_key(out, "win_rate", rep.base.win_rate, first);
  append_key(out, "profit_factor", rep.base.profit_factor, first);
  append_key(out, "total_trades", rep.base.total_trades, first);
  append_key(out, "downside_deviation_annualized", rep.base.downside_deviation_annualized, first);
  append_key(out, "var_95", rep.downside.var_95, first);
  append_key(out, "var_99", rep.downside.var_99, first);
  append_key(out, "cvar_95", rep.downside.cvar_95, first);
  append_key(out, "cvar_99", rep.downside.cvar_99, first);
  append_key(out, "max_drawdown_recovery_bars", rep.max_drawdown_recovery_bars, first);
  append_key(out, "time_in_drawdown_pct", rep.time_in_drawdown_pct, first);
  append_key(out, "num_drawdown_periods", rep.drawdowns.size(), first);
  append_key(out, "num_yearly_periods", rep.yearly_returns.size(), first);
  append_key(out, "num_monthly_periods", rep.monthly_returns.size(), first);
  out += '}';
  return Result<std::string>::ok(std::move(out));
}

} // namespace serialization
} // namespace quant
