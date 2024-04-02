from cocotb.triggers import Join, Combine
from pyuvm import *
import random
import cocotb
import pyuvm
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from utils_spi import SpiBfm,Ops,spi_prediction

class SpiSeqItem(uvm_sequence_item):
    def __init__(self, name, address, data, op):
        super().__init__(name)
        self.addr = address
        self.data = data
        self.op = Ops(op)

    def randomize_data(self):
        self.data = random.randint(0, 255)

    def __eq__(self, other):
        same = self.data == other.data
        return same

    def __str__(self):
        return f"{self.get_name()} : ADDR: 0x{self.addr:02x} \
        OP: {self.op.name} ({self.op.value}) DATA: 0x{self.data:02x}"

class SpiWR0Seq(uvm_sequence):
    async def body(self):
        cmd_tr = SpiSeqItem("cmd_tr", 0x0, 0x3c, Ops.WR)
        await self.start_item(cmd_tr)
        """cmd_tr.randomize_data()"""
        await self.finish_item(cmd_tr)

class SpiWR4Seq(uvm_sequence):
    async def body(self):
        cmd_tr = SpiSeqItem("cmd_tr", 0x4, 0x0, Ops.WR)
        await self.start_item(cmd_tr)
        """cmd_tr.randomize_data()"""
        await self.finish_item(cmd_tr)

class SpiWRSeq(uvm_sequence):
    async def body(self):
        cmd_tr = SpiSeqItem("cmd_tr", 0xb, 0xab, Ops.WR)
        await self.start_item(cmd_tr)
        """cmd_tr.randomize_data()"""
        await self.finish_item(cmd_tr)

class SpiRDSeq(uvm_sequence):
    async def body(self):
        cmd_tr = SpiSeqItem("cmd_tr", 0x0, 0xaa, Ops.RD)
        await self.start_item(cmd_tr)
        """cmd_tr.randomize_data()"""
        await self.finish_item(cmd_tr)

class TestSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        spiwrtest = SpiWR0Seq("spiwrtest")
        await spiwrtest.start(seqr)

class TestWrSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        spiwr0 = SpiWR0Seq("spiwr0")
        spird = SpiRDSeq("spird")
        await spiwr0.start(seqr)
        await spird.start(seqr)

class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = SpiBfm()

    async def launch_tb(self):
        await self.bfm.reset()
        self.bfm.start_bfm()

    async def run_phase(self):
        await self.launch_tb()
        uvm_root().logger.info(f"LAUNCH")
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.addr, cmd.data, cmd.op)
            uvm_root().logger.info(f"RUN PHASE addr: {cmd.addr} data: {cmd.data} op: {cmd.op}")
            result = await self.bfm.get_result()
            self.ap.write(result)
            uvm_root().logger.info(f"GET RESULT: {result}")
            self.seq_item_port.item_done()
            uvm_root().logger.info(f"RUN PHASE LAUNCH DONE")

class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = SpiBfm()
        self.get_method = getattr(self.bfm, self.method_name)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.logger.debug(f"MONITORED {datum}")
            self.ap.write(datum)

class Scoreboard(uvm_component):

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)

        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.result_get_port = uvm_get_port("result_get_port", self)

        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def check_phase(self):
        self.logger.info(f"CHECK SCB PHASE")
        passed = True
        while True:
            self.logger.info(f"CHECK SOMETHING")
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                break
            else:
                result_success, data_read = self.result_get_port.try_get()
                if not result_success:
                    self.logger.critical(f"result {data_read} had no command")
                else:
                    (addr, data, op_numb) = cmd
                    if op_numb == 1:
                        predicted_data = data_read
                        self.logger.info(f"WDATA  {predicted_data} ")
                    if op_numb == 2:
                        if predicted_data == data_read:
                            self.logger.info(f"PASSED: 0x{predicted_data} ="
                                             f" 0x{data_read}")
                        else:
                            self.logger.error(f"FAILED: "
                                              f"ACTUAL:   0x{data_read} "
                                              f"EXPECTED: 0x{predicted_data}")
                            passed = False
        assert passed

class SpiEnv(uvm_env):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.driver.ap.connect(self.scoreboard.result_export)

@pyuvm.test()
class BasicTest(uvm_test):
    def build_phase(self):
        uvm_root().logger.info(f"BUILD ENV")
        self.env = SpiEnv("env", self)

    def end_of_elaboration_phase(self):
        uvm_root().logger.info(f"CREATE TestSeq")
        self.test_all = TestSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()
        uvm_root().logger.info(f"START TEST")
        await self.test_all.start()
        uvm_root().logger.info(f"END TEST")
        self.drop_objection()

@pyuvm.test()
class WrDataTest(BasicTest):

    def build_phase(self):
        uvm_factory().set_type_override_by_type(TestSeq, TestWrSeq)
        super().build_phase()