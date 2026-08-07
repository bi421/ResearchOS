# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# Backtesting Core Implementation TODO

## Phase 0: Models (quant_engine/models.py)
- [x] Add frozen dataclass: Signal
- [x] Add frozen dataclass: Order
- [x] Add frozen dataclass: OrderFill
- [x] Add frozen dataclass: Position
- [x] Add frozen dataclass: Trade
- [x] Add periods_per_year helper mapping
- [x] Extend SimulationResult with trades/signals/positions/execution_stats

## Phase 1: Strategy Evaluation Interface (quant_engine/strategy.py)
- [x] Create StrategyEvaluationInterface (abstract)
- [x] Create BuyAndHoldStrategy (baseline)

## Phase 2: Execution Simulation Layer (quant_engine/execution.py)
- [x] Create ExecutionSimulationLayer
- [x] Order creation from signals
- [x] Fill logic with commission/slippage
- [x] Position tracking (realized/unrealized PnL)
- [x] Trade generation
- [x] Deterministic equity curve from trades

## Phase 3: Replay Engine (quant_engine/replay.py)
- [x] Create ReplayEngine
- [x] Chronological bar iteration
- [x] No-lookahead (as_of)
- [x] Strategy + execution integration

## Phase 4: Integration
- [x] Update PythonQuantBackend.run_simulation to use replay pipeline
- [x] Extend SimulationResult with trades/signals/positions
- [x] Update quant_engine/__init__.py exports
- [x] Update interface.py if needed

## Phase 5: Tests
- [x] deterministic replay (same dataset → same result)
- [x] no-lookahead
- [x] commission correctness
- [x] slippage correctness
- [x] trade generation
- [x] position accounting
- [x] dataset sensitivity
- [x] provenance
- [x] Verify existing tests pass

## Phase 6: Report
- [x] Verify all tests pass
- [x] Generate report
