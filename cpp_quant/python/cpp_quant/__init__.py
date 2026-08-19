"""
C++ Quant Engine for ResearchOS
"""
try:
    from .wrapper import CppQuant, __version__
except ImportError:
    print("?? C++ engine not available. Install/compile it first.")
    CppQuant = None
    __version__ = "0.0.0"

