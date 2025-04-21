from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os
import importlib.resources
import sys

# Get the path to the cxxrtl runtime
RUNTIME_DIR = importlib.resources.files("yowasp_yosys") / "share/include/backends/cxxrtl/runtime"
SOURCE_DIR = importlib.resources.files("my_design") / "sim"
BUILD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the extension
extensions = [
    Extension(
        "models",
        ["models.pyx"],
        include_dirs=[
            np.get_include(),
            str(RUNTIME_DIR),
            str(SOURCE_DIR),
            str(BUILD_DIR),
            str(SOURCE_DIR / "vendor"),
        ],
        language="c++",
        extra_compile_args=["-std=c++17", "-O3", "-fbracket-depth=1024"],
    )
]

# Setup
setup(
    name="cython_models",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,
            "embedsignature": True,
        },
    ),
)