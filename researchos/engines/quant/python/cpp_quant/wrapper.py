import sys
from pathlib import Path

# Determine the correct build directory dynamically
# __file__ is in researchos/engines/quant/python/cpp_quant/wrapper.py
# We need to go up 4 levels to reach researchos/engines/quant/
base_dir = Path(__file__).parent.parent.parent.parent
build_dir = base_dir / "build" / "Release"
if build_dir.exists():
    sys.path.insert(0, str(build_dir))
else:
    # fallback: try root-level cpp_quant/build/Release
    root_build = Path(__file__).parent.parent.parent.parent.parent / "cpp_quant" / "build" / "Release"
    if root_build.exists():
        sys.path.insert(0, str(root_build))
    else:
        print("⚠️ C++ build directory not found. Please compile cpp_quant first.")

try:
    from _core import QuantEngine
except ImportError as e:
    raise RuntimeError("C++ engine not available. Compile it first.") from e


class CppQuant(QuantEngine):
    """Python wrapper for C++ Quant Engine."""

    pass
