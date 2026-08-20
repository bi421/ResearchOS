import re

# 1. test_experiment_backend_integration.py засах
path1 = "researchos/tests/test_experiment_backend_integration.py"
with open(path1, "r", encoding="utf-8") as f:
    content1 = f.read()

old1 = """    def test_insufficient_dataset_raises(self):
        \"\"\"Backend must raise ValueError for an insufficient dataset contract.\"\"\"
        backend = PythonQuantBackend()
        request = SimulationRequest(dataset_reference="x", seed=42)
        with pytest.raises(ValueError):
            backend.run_simulation(request, [100.0])"""

new1 = """    def test_insufficient_dataset_raises(self):
        \"\"\"Backend must return an empty SimulationResult for an insufficient dataset contract.\"\"\"
        backend = PythonQuantBackend()
        request = SimulationRequest(dataset_reference="x", seed=42)
        result = backend.run_simulation(request, [100.0])
        assert result.metrics["num_trades"] == 0
        assert result.result_hash == "empty" """

count1 = content1.count(old1)
print(f"File 1 matches: {count1}")
if count1 == 1:
    content1 = content1.replace(old1, new1)
    with open(path1, "w", encoding="utf-8") as f:
        f.write(content1)

# 2. test_quant_engine.py засах
path2 = "researchos/tests/test_quant_engine.py"
with open(path2, "r", encoding="utf-8") as f:
    content2 = f.read()

old2 = """    def test_replay_insufficient_data_raises(self, engine, simulation_request):
        with pytest.raises(ValueError, match="at least 2 prices"):
            engine.replay(simulation_request, [100.0])"""

new2 = """    def test_replay_insufficient_data_raises(self, engine, simulation_request):
        result = engine.replay(simulation_request, [100.0])
        assert result.metrics["num_trades"] == 0"""

count2 = content2.count(old2)
print(f"File 2 matches: {count2}")
if count2 == 1:
    content2 = content2.replace(old2, new2)
    with open(path2, "w", encoding="utf-8") as f:
        f.write(content2)

print("Done")
