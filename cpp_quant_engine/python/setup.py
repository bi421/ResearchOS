# setup.py
from setuptools import setup, Extension, find_packages
import os
import sys

build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", "Release"))

cpp_quant_engine = Extension(
    "cpp_quant_engine.cpp_quant_backend",
    sources=[],
    libraries=["quant_engine"],
    library_dirs=[build_dir],
    include_dirs=[os.path.join(os.path.dirname(__file__), "..", "include")],
    language="c++",
    extra_compile_args=["/std:c++17"] if sys.platform == "win32" else ["-std=c++17"],
)

setup(
    name="cpp_quant_engine",
    version="0.1.0",
    description="C++ Quant Engine Python Bindings",
    packages=find_packages(where="."),
    package_dir={"": "."},
    ext_modules=[cpp_quant_engine],
    python_requires=">=3.10",
    install_requires=["numpy>=1.24", "pandas>=2.0"],
)
