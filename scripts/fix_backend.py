with open("researchos/quant_engine/backend.py", "r", encoding="utf-8") as f:
    content = f.read()

new_method = """    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
        timeframe: str = "1d",
        asset_class: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, float]:
        # Determine asset_class from symbol if not given
        if asset_class is None and symbol is not None:
            from researchos.instruments.metadata import InstrumentMetadataRegistry
            registry = InstrumentMetadataRegistry()
            asset_class = registry.get_asset_class(symbol)
        if asset_class is None:
            asset_class = "equity"

        periods_per_year = periods_per_year_from_timeframe(timeframe, asset_class)
        metrics = compute_all_metrics(
            returns,
            equity_curve,
            risk_free_rate,
            calculation_version=calculation_version,
            periods_per_year=periods_per_year,
        )
        if "max_drawdown" in metrics:
            metrics["max_drawdown"] = round(float(metrics["max_drawdown"]), 8)
            if metrics["max_drawdown"] != 0.0 and "mean_return" in metrics:
                metrics["calmar_ratio"] = (
                    float(metrics["mean_return"]) * periods_per_year / abs(metrics["max_drawdown"])
                )
        return metrics
"""

# Find the old method and replace it
lines = content.splitlines()
start_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith("def calculate_metrics("):
        start_idx = i
        break

if start_idx is not None:
    # Find end: next line that starts with '    def ' after start_idx
    end_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].startswith("    def "):
            end_idx = j
            break
    if end_idx is None:
        end_idx = len(lines)
    # Replace lines from start_idx to end_idx-1 with new_method
    new_lines = lines[:start_idx] + new_method.splitlines() + lines[end_idx:]
    content = "\n".join(new_lines)
    with open("researchos/quant_engine/backend.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ calculate_metrics method fixed.")
else:
    print("❌ calculate_metrics not found.")
