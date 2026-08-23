import sys
from pathlib import Path

# Build directory detection
base_dir = Path(__file__).parent.parent.parent
build_dir = base_dir / "build" / "Release"

if not build_dir.exists():
    alt_build = Path(__file__).parent.parent.parent.parent / "researchos" / "engines" / "quant" / "build" / "Release"
    if alt_build.exists():
        build_dir = alt_build
    else:
        raise RuntimeError(f"Build directory not found. Tried: {build_dir} and {alt_build}")

if not any(build_dir.glob("*.pyd")):
    raise RuntimeError(f"No .pyd files found in {build_dir}")

# Add build directory to sys.path
sys.path.insert(0, str(build_dir))

# Import the module
try:
    import cpp_quant_core as core
except ImportError as e:
    raise RuntimeError(f"Failed to import cpp_quant_core from {build_dir}: {e}")

# Find the engine class
if hasattr(core, "QuantEngine"):
    QuantEngine = core.QuantEngine
else:
    # Print available attributes for debugging
    attrs = [a for a in dir(core) if not a.startswith("_")]
    raise RuntimeError(f"'QuantEngine' not found in cpp_quant_core. Available: {attrs}")


class CppQuant(QuantEngine):
    """Python wrapper for C++ Quant Engine."""

    pass
