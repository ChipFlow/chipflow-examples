import os
import sys
import importlib.resources


OUTPUT_DIR  = "./build/sim"
SOURCE_DIR  = importlib.resources.files("my_design") / "sim"
RUNTIME_DIR = importlib.resources.files("yowasp_yosys") / "share/include/backends/cxxrtl/runtime"

ZIG_CXX  = f"{sys.executable} -m ziglang c++"
CXXFLAGS = f"-O3 -g -std=c++17 -Wno-array-bounds -Wno-shift-count-overflow -fbracket-depth=1024"
INCLUDES = f"-I {OUTPUT_DIR} -I {SOURCE_DIR}/vendor -I {RUNTIME_DIR}"


def task_build_sim_cxxrtl():
    return {
        "actions": [f"cd {OUTPUT_DIR} && pdm run yowasp-yosys sim_soc.ys"],
        "targets": [f"{OUTPUT_DIR}/sim_soc.cc", f"{OUTPUT_DIR}/sim_soc.h"],
        "file_dep": [f"{OUTPUT_DIR}/sim_soc.ys", f"{OUTPUT_DIR}/sim_soc.il"],
    }


def task_build_sim():
    exe = ".exe" if os.name == "nt" else ""

    return {
        "actions": [
            f"{ZIG_CXX} {CXXFLAGS} {INCLUDES} -o {OUTPUT_DIR}/sim_soc{exe} "
            f"{OUTPUT_DIR}/sim_soc.cc {SOURCE_DIR}/main.cc {SOURCE_DIR}/models.cc"
        ],
        "targets": [
            f"{OUTPUT_DIR}/sim_soc{exe}"
        ],
        "file_dep": [
            f"{OUTPUT_DIR}/sim_soc.cc",
            f"{OUTPUT_DIR}/sim_soc.h",
            f"{SOURCE_DIR}/main.cc",
            f"{SOURCE_DIR}/models.cc",
            f"{SOURCE_DIR}/models.h",
            f"{SOURCE_DIR}/vendor/nlohmann/json.hpp",
            f"{SOURCE_DIR}/vendor/cxxrtl/cxxrtl_server.h",
        ],
    }


def task_build_cython_models():
    return {
        "actions": [
            f"mkdir -p {OUTPUT_DIR}/cython_models",
            f"cp {SOURCE_DIR}/cython_models/models.pyx {OUTPUT_DIR}/cython_models/",
            f"cp {SOURCE_DIR}/cython_models/cxxrtl_wrap.h {OUTPUT_DIR}/cython_models/",
            f"cp {SOURCE_DIR}/cython_models/setup.py {OUTPUT_DIR}/cython_models/",
            f"cd {OUTPUT_DIR}/cython_models && pdm run python setup.py build_ext --inplace"
        ],
        "targets": [
            f"{OUTPUT_DIR}/cython_models/models.*.so"  # Platform-dependent extension
        ],
        "file_dep": [
            f"{SOURCE_DIR}/cython_models/models.pyx",
            f"{SOURCE_DIR}/cython_models/cxxrtl_wrap.h",
            f"{SOURCE_DIR}/cython_models/setup.py",
            f"{OUTPUT_DIR}/sim_soc.h",
        ],
    }


def task_build_cython_sim():
    exe = ".exe" if os.name == "nt" else ""
    
    import sysconfig
    python_include = sysconfig.get_path('include')
    python_lib = sysconfig.get_config_var('LIBDIR')
    
    cython_includes = f"-I {SOURCE_DIR}/cython_models -I {python_include}"
    cython_libs = f"-L {python_lib} -lpython{sysconfig.get_config_var('VERSION')}"

    return {
        "actions": [
            f"{ZIG_CXX} {CXXFLAGS} {INCLUDES} {cython_includes} "
            f"-o {OUTPUT_DIR}/cython_sim{exe} {OUTPUT_DIR}/sim_soc.cc {SOURCE_DIR}/cython_main.cc "
            f"{cython_libs}"
        ],
        "targets": [
            f"{OUTPUT_DIR}/cython_sim{exe}"
        ],
        "file_dep": [
            f"{OUTPUT_DIR}/sim_soc.cc",
            f"{OUTPUT_DIR}/sim_soc.h",
            f"{SOURCE_DIR}/cython_main.cc",
            f"{SOURCE_DIR}/cython_models/cxxrtl_wrap.h",
            f"{SOURCE_DIR}/vendor/nlohmann/json.hpp",
            f"{SOURCE_DIR}/vendor/cxxrtl/cxxrtl_server.h",
        ],
        "task_dep": [
            "build_cython_models"
        ]
    }