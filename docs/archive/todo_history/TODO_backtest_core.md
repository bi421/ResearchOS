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

# Real Backtesting Core Implementation — TODO

## Phase 0: Models (quant_engine/models.py)
- [ ] Extend SimulationResult with signals / positions / execution_stats
- [ ] Include new fields in compute_result_hash, to_dict, from_dict (deterministic + provenance)

## Phase 1: Strategy Evaluation Interface (quant_engine/strategy.py) [CREATE]
- [ ] StrategyEvaluationInterface (ABC) — research only, no broker/execution/live, no decision_engine
- [ ] BuyAndHoldStrategy — baseline to validate the pipeline

## Phase 2: Execution Simulation Layer (quant_engine/execution.py) [CREATE]
- [ ] ExecutionSimulationLayer
- [ ] order creation from signals
- [ ] fill simulation (commission + slippage, no randomness)
- [ ] position tracking (realized + unrealized PnL)
- [ ] trade generation (round-trip records)
- [ ] deterministic equity curve

## Phase 3: Replay Engine (quant_engine/replay.py) [CREATE]
- [ ] ReplayEngine
- [ ] chronological candle processing
- [ ] no lookahead (as_of / history window)
- [ ] bar → strategy → signal → execution feed
- [ ] end-of-data liquidation

## Phase 4: Integration
- [ ] PythonQuantBackend.run_simulation → replay pipeline (primary path via strategy param)
- [ ] Passive path retained as backward-compatible fallback
- [ ] SimulationResult carries signals/trades/positions/execution_stats
- [ ] Runner metadata exposes trades/signals/positions/execution_stats (orchestrator only)
- [ ] quant_engine/__init__.py exports updated

## Phase 5: Tests (researchos/tests/test_backtest_core.py) [CREATE]
- [ ] deterministic replay
- [ ] no-lookahead
- [ ] commission calculation
- [ ] slippage calculation
- [ ] trade generation
- [ ] position accounting
- [ ] provenance
- [ ] dataset sensitivity
- [ ] runner integration (replay path)

## Phase 6: Verification
- [ ] Run full suite — all existing + new tests pass
- [ ] Generate BACKTESTING_CORE_REPORT.md

