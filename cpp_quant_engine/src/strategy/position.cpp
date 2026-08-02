#include "quant/strategy/position.h"

#include <algorithm>

namespace quant {
namespace strategy {

void OpenPosition::update_mfe_mae(double high, double low) {
  if (is_long()) {
    mfe = std::max(mfe, high - open_raw);
    mae = std::min(mae, low - open_raw);
  } else {
    mfe = std::max(mfe, open_raw - low);
    mae = std::min(mae, open_raw - high);
  }
}

void OpenPosition::move_stop_to_break_even() {
  stop_loss = open_raw;
  break_even_moved = true;
}

void OpenPosition::ratchet_trailing(double best_price) {
  if (!trailing_active || trailing_distance <= 0.0) return;
  const double new_stop =
      is_long() ? best_price - trailing_distance : best_price + trailing_distance;
  if (is_long()) {
    if (new_stop > stop_loss) stop_loss = new_stop;
  } else {
    if (new_stop < stop_loss) stop_loss = new_stop;
  }
}

} // namespace strategy
} // namespace quant
