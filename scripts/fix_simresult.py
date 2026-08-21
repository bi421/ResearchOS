with open("researchos/quant_engine/backend.py", encoding="utf-8") as f:
    content = f.read()

old1 = """            return SimulationResult(
                result_hash="empty",
                metrics={
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "winrate": 0.0,
                    "num_trades": 0,
                },
                trades=[],
                input_hash=request.compute_input_hash(),
                calculation_version=calculation_version,
                execution_timestamp=utc_now(),
                dataset_hash="empty",
                engine_version=self.__class__.__name__
            )"""

new1 = """            return SimulationResult(
                simulation_id=request.compute_input_hash(),
                dataset_reference=request.dataset_reference,
                result_hash="empty",
                metrics={
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "winrate": 0.0,
                    "num_trades": 0,
                },
                trades=[],
                input_hash=request.compute_input_hash(),
                calculation_version=calculation_version,
                execution_timestamp=utc_now().isoformat(),
            )"""

old2 = """            return SimulationResult(
                result_hash="empty_backtest",
                metrics={
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "winrate": 0.0,
                    "num_trades": 0,
                },
                trades=[],
                input_hash=request.compute_input_hash(),
                calculation_version=calculation_version,
                execution_timestamp=utc_now(),
                dataset_hash="empty",
                engine_version=self.__class__.__name__
            )"""

new2 = """            return SimulationResult(
                simulation_id=request.compute_input_hash(),
                dataset_reference=request.dataset_reference,
                result_hash="empty_backtest",
                metrics={
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "winrate": 0.0,
                    "num_trades": 0,
                },
                trades=[],
                input_hash=request.compute_input_hash(),
                calculation_version=calculation_version,
                execution_timestamp=utc_now().isoformat(),
            )"""

count1 = content.count(old1)
count2 = content.count(old2)
print(f"Block 1 matches: {count1}, Block 2 matches: {count2}")

if count1 == 1:
    content = content.replace(old1, new1)
if count2 == 1:
    content = content.replace(old2, new2)

with open("researchos/quant_engine/backend.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
