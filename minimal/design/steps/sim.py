import os
import importlib.resources
from contextlib import contextmanager
from pathlib import Path
from pprint import pformat

from doit.cmd_base import TaskLoader2, loader
from doit.doit_cmd import DoitMain
from doit.task import dict_to_task

from amaranth import *
from amaranth.back import rtlil
from chipflow_lib.steps.sim import SimStep
from chipflow_lib import ChipFlowError

from ..design import MySoC
from ..sim.doit_build import VARIABLES, TASKS, DOIT_CONFIG

EXE = ".exe" if os.name == "nt" else ""

@contextmanager
def common():
    chipflow_lib = importlib.resources.files('chipflow_lib')
    common = chipflow_lib.joinpath('common', 'sim')
    with importlib.resources.as_file(common) as f:
        yield f

@contextmanager
def source():
    sourcedir = importlib.resources.files("minimal")
    sim_src = sourcedir.joinpath('design','sim')
    with importlib.resources.as_file(sim_src) as f:
        yield f

@contextmanager
def runtime():
    yowasp = importlib.resources.files("yowasp_yosys")
    runtime = yowasp.joinpath('share', 'include', 'backends', 'cxxrtl', 'runtime')
    with importlib.resources.as_file(runtime) as f:
        yield f


class ContextTaskLoader(TaskLoader2):
    def __init__(self, config, tasks, context):
        self.config = config
        self.tasks = tasks
        self.subs = context
        super().__init__()

    def load_doit_config(self):
        return loader.load_doit_config(self.config)

    def load_tasks(self, cmd, pos_args):
        task_list = []
        # substitute
        for task in self.tasks:
            d = {}
            for k,v in task.items():
                match v:
                    case str():
                        d[k.format(**self.subs)] = v.format(**self.subs)
                    case list():
                        d[k.format(**self.subs)] = [i.format(**self.subs) for i in v]
                    case _:
                        raise ChipFlowError("Unexpected task definition")
            print(f"adding task: {pformat(d)}")
            task_list.append(dict_to_task(d))
        return task_list


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
    def __init__(self, config):
        platform = SimPlatform()

        super().__init__(config, platform)

    def build(self):
        my_design = MySoC()

        self.platform.build(my_design)
        with common() as common_dir, source() as source_dir, runtime() as runtime_dir:
            context = {
                "COMMON_DIR": common_dir,
                "SOURCE_DIR": source_dir,
                "RUNTIME_DIR": runtime_dir,
                "EXE": EXE,
                }
            for k,v in VARIABLES.items():
                context[k] = v.format(**context)
            print(f"substituting:\n{pformat(context)}")
            DoitMain(ContextTaskLoader(DOIT_CONFIG, TASKS, context)).run(["build_sim"])
