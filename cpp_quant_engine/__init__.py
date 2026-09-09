"""Source-tree bootstrap for the C++ Quant Engine Python package.

The compiled extension and its Python facade live under
``cpp_quant_engine/python/cpp_quant_engine`` because CMake writes the native
module there.  The ResearchOS root package is installed from the repository
root, so Python otherwise cannot discover that nested package.

Extending ``__path__`` here makes the canonical package importable from the
ResearchOS source tree without ad-hoc ``sys.path`` mutations in scripts.
After CMake builds ``cpp_quant_backend``, imports such as
``from cpp_quant_engine.backend import CppQuantEngineBackend`` resolve to the
same Python facade used by the C++ integration tests.
"""

from __future__ import annotations

from pathlib import Path

# Make the canonical Python facade (and the generated .pyd/.so) a submodule
# location of this source-tree package.
_python_package = Path(__file__).resolve().parent / "python" / "cpp_quant_engine"
if _python_package.is_dir():
    _path = str(_python_package)
    if _path not in __path__:
        __path__.append(_path)
