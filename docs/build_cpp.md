# Building the C++ Quant Engine

The C++ quant engine provides a high-performance, bit-exact acceleration
path for `run_ml_backtest_cpp`. It is **optional** — the Python reference
implementation is always available and serves as the scientific source of
truth.

## Prerequisites

- **CMake** >= 3.20
- **C++20** compiler (MSVC on Windows, GCC 10+ or Clang 11+ on Linux/macOS)
- **pybind11** >= 2.10
- **Python** >= 3.10 development headers

### Installing pybind11

```bash
pip install pybind11
```

## Build Methods

### Method 1: setuptools (recommended for development)

From the `researchos/engines/quant/` directory:

```bash
cd researchos/engines/quant
python setup.py build_ext --inplace
```

This produces `cpp_quant.pyd` (Windows) or `cpp_quant.so` (Linux/macOS)
in the same directory.

### Method 2: CMake (recommended for production)

```bash
cd researchos/engines/quant
cmake -B build -DBUILD_PYTHON_BINDINGS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

The compiled module will be at:
```
researchos/engines/quant/cpp_quant.cp{version}-{platform}.pyd
```

### Method 3: scikit-build (integrated with pyproject.toml)

Add to your `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel", "scikit-build-core>=0.10", "pybind11>=2.10"]
build-backend = "scikit_build_core.build"

[project]
optional-dependencies = ["cpp"] = ["pybind11>=2.10"]
```

Then build with:

```bash
pip install -e .[cpp]
```

## Verification

After building, verify the engine is available:

```bash
python -c "from researchos.engines.quant.cpp_quant import run_ml_backtest_cpp; print('C++ engine available')"
```

## Parity Testing

The mandatory parity test (`researchos/engines/quant/parity_test.py`) must
pass with **zero tolerance** for floating-point differences:

```bash
python -m pytest researchos/engines/quant/parity_test.py -v
```

If the C++ engine is not built, the test will **FAIL** (not skip) with:

```
C++ engine not available — this is a CRITICAL failure.
Build the C++ engine before deploying.
```

## Determinism Guarantee

The C++ engine must produce **bit-exact** results identical to the Python
reference implementation. Any divergence in floating-point output is a
CRITICAL bug and must be fixed before deployment.

The parity test compares IEEE-754 representations via `struct.pack` to
catch:
- Different calculation order (Kahan summation vs naive)
- FMA (fused multiply-add) vs separate multiply+add
- Extended precision (x87 80-bit) vs SSE2 64-bit
- Compiler optimization reordering

## CI Integration

The parity test must run in CI on every commit. Add to `.github/workflows/ci.yml`:

```yaml
- name: Build C++ engine
  run: |
    cd researchos/engines/quant
    python setup.py build_ext --inplace

- name: Run parity tests
  run: python -m pytest researchos/engines/quant/parity_test.py -v
```

## Troubleshooting

### "C++ engine not available"

- Ensure `cpp_quant.pyd` (Windows) or `cpp_quant.so` (Linux/macOS) exists
  in `researchos/engines/quant/`
- Ensure the file is importable: `python -c "import cpp_quant"`
- Check that the Python version matches the compiled extension
  (e.g., `cp314` = Python 3.14)

### "BIT EXACT MISMATCH"

- Rebuild the C++ engine with `-O3 -march=native` removed
- Ensure both compilers use the same floating-point model
- Check for FMA flags (`-mfma`) that may enable fused multiply-add
- Verify no `#pragma float_control(precise, on)` or similar is needed
