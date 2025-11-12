from chipflow.platform import SoftwareStep
from ..software import doit_build


class MySoftwareStep(SoftwareStep):
    doit_build_module = doit_build
