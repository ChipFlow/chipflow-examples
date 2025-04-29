from chipflow_lib.steps.sim import SimStep

from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import connect, flipped
from amaranth.back import rtlil

from ..design import MySoC
from ..sim import doit_build

import os
import sys
import importlib.resources
from pathlib import Path

# Get the path to the cxxrtl runtime
RUNTIME_DIR = importlib.resources.files("yowasp_yosys") / "share/include/backends/cxxrtl/runtime"

class SimPlatform:

    def __init__(self):
        self.build_dir = os.path.join(os.environ['CHIPFLOW_ROOT'], 'build', 'sim')
        self.extra_files = dict()

    def add_file(self, filename, content):
        if not isinstance(content, (str, bytes)):
            content = content.read()
        self.extra_files[filename] = content

    def build(self, e):
        Path(self.build_dir).mkdir(parents=True, exist_ok=True)

        output = rtlil.convert(e, name="sim_top", ports=None, platform=self)

        top_rtlil = Path(self.build_dir) / "sim_soc.il"
        with open(top_rtlil, "w") as rtlil_file:
            rtlil_file.write(output)
        top_ys = Path(self.build_dir) / "sim_soc.ys"
        with open(top_ys, "w") as yosys_file:
            for extra_filename, extra_content in self.extra_files.items():
                extra_path = Path(self.build_dir) / extra_filename
                with open(extra_path, "w") as extra_file:
                    extra_file.write(extra_content)
                if extra_filename.endswith(".il"):
                    print(f"read_rtlil {extra_path}", file=yosys_file)
                else:
                    # FIXME: use -defer (workaround for YosysHQ/yosys#4059)
                    print(f"read_verilog {extra_path}", file=yosys_file)
            print("read_rtlil sim_soc.il", file=yosys_file)
            print("hierarchy -top sim_top", file=yosys_file)
            print("write_cxxrtl -header sim_soc.cc", file=yosys_file)


class MySimStep(SimStep):
    doit_build_module = doit_build

    def __init__(self, config):
        platform = SimPlatform()
        use_cython_default = config.get("sim", {}).get("default_use_cython", True)
        self.use_cython = config.get("sim", {}).get("use_cython", use_cython_default)
        self.use_cxxrtl_capi = config.get("sim", {}).get("use_cxxrtl_capi", False)
        self.config = config
        print(f"Simulator config: {config.get('sim', {})}")
        print(f"Using Cython: {self.use_cython}")
        print(f"Using CXXRTL CAPI: {self.use_cxxrtl_capi}")

        super().__init__(config, platform)
        
    # Add this method to provide a CLI entry point
    def run_cli(self, args):
        self.run()

    def build(self):
        my_design = MySoC()

        self.platform.build(my_design)
        
        # Build the simulator
        self.doit_build()
        
        # Print a message about the simulation mode
        sim_mode = "Cython"
        if self.use_cxxrtl_capi:
            sim_mode += " + CXXRTL CAPI"
        elif not self.use_cython:
            sim_mode = "C++"
        print(f"Using {sim_mode} based simulation")
            
    def run(self):
        import subprocess
        import os
        
        # Make sure software is built
        if not os.path.exists(os.path.join("build", "software", "software.bin")):
            from chipflow_lib.steps.software import SoftwareStep
            sw_step = SoftwareStep(self.config)
            sw_step.build()
        
        # Decide which simulator to build/run
        if self.use_cython:
            if self.use_cxxrtl_capi:
                self._build_cython_capi_simulator()
                cmd = "cd build/sim && ./cython_capi_sim"
            else:
                self._build_cython_simulator()
                cmd = "cd build/sim && ./cython_sim"
        else:
            cmd = "cd build/sim && ./sim_soc"
            
        subprocess.run(cmd, shell=True, check=True)
    
    def _build_cython_simulator(self):
        """Build the standard Cython simulator"""
        import subprocess
        import os
        import sysconfig
        
        if os.path.exists(os.path.join("build", "sim", "cython_sim")):
            print("Cython simulator already built")
            return
            
        print("Building Cython simulator...")
        
        # First make sure the directory structure exists
        os.makedirs(os.path.join("build", "sim", "cython_models"), exist_ok=True)
        
        # Copy Cython model files
        src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sim", "cython_models")
        for filename in ["models.pyx", "cxxrtl_wrap.h", "setup.py"]:
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join("build", "sim", "cython_models", filename)
            with open(src_file, 'r') as src, open(dst_file, 'w') as dst:
                dst.write(src.read())
        
        # Build Cython extension
        subprocess.run(
            "cd build/sim/cython_models && python setup.py build_ext --inplace",
            shell=True, check=True
        )
        
        # Build Cython simulator
        py_include = sysconfig.get_path('include')
        py_lib = sysconfig.get_config_var('LIBDIR')
        py_version = sysconfig.get_config_var('VERSION')
        
        build_cmd = (
            f"{sys.executable} -m ziglang c++ -O3 -g -std=c++17 -Wno-array-bounds "
            f"-Wno-shift-count-overflow -fbracket-depth=1024 "
            f"-I build/sim -I my_design/sim/vendor "
            f"-I {RUNTIME_DIR} -I build/sim/cython_models -I {py_include} "
            f"-o build/sim/cython_sim build/sim/sim_soc.cc my_design/sim/cython_main.cc "
            f"-L {py_lib} -lpython{py_version}"
        )
        subprocess.run(build_cmd, shell=True, check=True)
    
    def _build_cython_capi_simulator(self):
        """Build the Cython simulator with CXXRTL CAPI"""
        import subprocess
        import os
        import sysconfig
        
        if os.path.exists(os.path.join("build", "sim", "cython_capi_sim")):
            print("Cython CAPI simulator already built")
            return
            
        print("Building Cython CAPI simulator...")
        
        # First make sure the directory structure exists
        os.makedirs(os.path.join("build", "sim", "cython_models"), exist_ok=True)
        
        # Copy Cython model files
        src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sim", "cython_models")
        for filename in ["models.pyx", "cxxrtl_wrap.h", "setup.py", "cxxrtl_capi.pyx", 
                         "cxxrtl_capi_wrap.h", "setup_capi.py", "cxxrtl_capi_module.py"]:
            src_file = os.path.join(src_dir, filename)
            if os.path.exists(src_file):
                dst_file = os.path.join("build", "sim", "cython_models", filename)
                with open(src_file, 'r') as src, open(dst_file, 'w') as dst:
                    dst.write(src.read())
        
        # Build Cython CAPI extension
        subprocess.run(
            "cd build/sim/cython_models && python setup_capi.py build_ext --inplace",
            shell=True, check=True
        )
        
        # Build Cython extension for models
        subprocess.run(
            "cd build/sim/cython_models && python setup.py build_ext --inplace",
            shell=True, check=True
        )
        
        # Build Cython CAPI simulator
        py_include = sysconfig.get_path('include')
        py_lib = sysconfig.get_config_var('LIBDIR')
        py_version = sysconfig.get_config_var('VERSION')
        
        build_cmd = (
            f"{sys.executable} -m ziglang c++ -O3 -g -std=c++17 -Wno-array-bounds "
            f"-Wno-shift-count-overflow -fbracket-depth=1024 "
            f"-I build/sim -I my_design/sim/vendor "
            f"-I {RUNTIME_DIR} -I build/sim/cython_models -I {py_include} "
            f"-o build/sim/cython_capi_sim build/sim/sim_soc.cc my_design/sim/cython_main.cc "
            f"-L {py_lib} -lpython{py_version}"
        )
        subprocess.run(build_cmd, shell=True, check=True)