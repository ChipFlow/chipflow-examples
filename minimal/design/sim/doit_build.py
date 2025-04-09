import os
import sys
import importlib.resources


OUTPUT_DIR  = "./build/sim"
COMMON_DIR  = importlib.resources.files("common") / "sim"
SOURCE_DIR  = importlib.resources.files("minimal") / "design/sim"
RUNTIME_DIR = importlib.resources.files("yowasp_yosys") / "share/include/backends/cxxrtl/runtime"

ZIG_CXX  = f"{sys.executable} -m ziglang c++"
CXXFLAGS = f"-O3 -g -std=c++17 -Wno-array-bounds -Wno-shift-count-overflow -fbracket-depth=1024"
INCLUDES = f"-I {OUTPUT_DIR} -I {COMMON_DIR} -I {COMMON_DIR}/vendor -I {RUNTIME_DIR}"


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
            f"{OUTPUT_DIR}/sim_soc.cc {SOURCE_DIR}/main.cc {COMMON_DIR}/models.cc"
        ],
        "targets": [
            f"{OUTPUT_DIR}/sim_soc{exe}"
        ],
        "file_dep": [
            f"{OUTPUT_DIR}/sim_soc.cc",
            f"{OUTPUT_DIR}/sim_soc.h",
            f"{SOURCE_DIR}/main.cc",
            f"{COMMON_DIR}/models.cc",
            f"{COMMON_DIR}/models.h",
            f"{COMMON_DIR}/vendor/nlohmann/json.hpp",
            f"{COMMON_DIR}/vendor/cxxrtl/cxxrtl_server.h",
        ],
    }
