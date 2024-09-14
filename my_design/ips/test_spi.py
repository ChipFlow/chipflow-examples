from amaranth import *
from amaranth.sim import Simulator, Tick

from .spi import SPIPeripheral, SPISignature
import unittest

class TestSpiPeripheral(unittest.TestCase):

    REG_CONFIG = 0x00
    REG_DIV = 0x04
    REG_SEND_DATA = 0x08
    REG_RECEIVE_DATA = 0x0C
    REG_STATUS = 0x10

    def _write_reg(self, dut, reg, value, width=4):
        for i in range(width):
            yield dut.bus.addr.eq(reg + i)
            yield dut.bus.w_data.eq((value >> (8 * i)) & 0xFF)
            yield dut.bus.w_stb.eq(1)
            yield Tick()
        yield dut.bus.w_stb.eq(0)

    def _check_reg(self, dut, reg, value, width=4):
        result = 0
        for i in range(width):
            yield dut.bus.addr.eq(reg + i)
            yield dut.bus.r_stb.eq(1)
            yield Tick()
            result |= (yield dut.bus.r_data) << (8 * i)
        yield dut.bus.r_stb.eq(0)
        self.assertEqual(result, value)

    def test_chip_select(self):
        dut = SPIPeripheral(name="dut")
        def testbench():
            yield from self._write_reg(dut, self.REG_CONFIG, 1<<2, 1)
            yield Tick()
            self.assertEqual((yield dut.spi_pins.csn_o), 0)
            yield from self._write_reg(dut, self.REG_CONFIG, 0<<2, 1)
            yield Tick()
            self.assertEqual((yield dut.spi_pins.csn_o), 1)

        sim = Simulator(dut)
        sim.add_clock(1e-5)
        sim.add_testbench(testbench)
        with sim.write_vcd("spi_cs_test.vcd", "spi_cs_test.gtkw"):
            sim.run()

    def test_xfer(self):
        dut = SPIPeripheral(name="dut")
        tests = [
            (13, 0x1C3, 0x333),
            (8, 0x66, 0x5A),
            (32, 0xDEADBEEF, 0xC0FFEE11)
        ]
        def testbench():
            for sck_idle, sck_edge in ((0, 0), (0, 1), (1, 0), (1, 1)):
                for width, d_send, d_recv in tests:
                    yield from self._write_reg(dut, self.REG_CONFIG, ((width - 1) << 3) | (sck_edge << 1) | (sck_idle), 4)
                    yield from self._write_reg(dut, self.REG_DIV, 1, 1)
                    yield Tick()
                    yield from self._check_reg(dut, self.REG_STATUS, 0, 1) # not full
                    yield from self._write_reg(dut, self.REG_SEND_DATA, (d_send << (32 - width)), 4)
                    yield Tick()
                    for i in reversed(range(width)):
                        if sck_edge:
                            yield dut.spi_pins.miso_i.eq((d_recv >> i) & 0x1)
                        else:
                            self.assertEqual((yield dut.spi_pins.mosi_o), (d_send >> i) & 0x1)
                        self.assertEqual((yield dut.spi_pins.sck_o), 0 ^ sck_idle)
                        yield Tick()
                        self.assertEqual((yield dut.spi_pins.sck_o), 0 ^ sck_idle)
                        if sck_edge:
                            self.assertEqual((yield dut.spi_pins.mosi_o), (d_send >> i) & 0x1)
                        else:
                            yield dut.spi_pins.miso_i.eq((d_recv >> i) & 0x1)
                        yield Tick()
                        self.assertEqual((yield dut.spi_pins.sck_o), 1 ^ sck_idle)
                        yield Tick()
                        self.assertEqual((yield dut.spi_pins.sck_o), 1 ^ sck_idle)
                        yield Tick()
                    yield Tick()
                    yield Tick()
                    yield from self._check_reg(dut, self.REG_STATUS, 1, 1) # full
                    yield from self._check_reg(dut, self.REG_RECEIVE_DATA, d_recv, 4) # received correct data
                    yield from self._check_reg(dut, self.REG_STATUS, 0, 1) # not full

        sim = Simulator(dut)
        sim.add_clock(1e-5)
        sim.add_testbench(testbench)
        with sim.write_vcd("spi_xfer_test.vcd", "spi_xfer_test.gtkw"):
            sim.run()

    def test_divider(self):
        dut = SPIPeripheral(name="dut")

        def testbench():
            width = 8
            d_send = 0x73
            divide = 13

            yield from self._write_reg(dut, self.REG_CONFIG, ((width - 1) << 3), 4)
            yield from self._write_reg(dut, self.REG_DIV, divide, 1)
            yield Tick()
            yield from self._check_reg(dut, self.REG_STATUS, 0, 1) # not full
            yield from self._write_reg(dut, self.REG_SEND_DATA, (d_send << (32 - width)), 4)
            yield Tick()
            for i in reversed(range(width)):
                self.assertEqual((yield dut.spi_pins.mosi_o),(d_send >> i) & 0x1)
                self.assertEqual((yield dut.spi_pins.sck_o), 0)
                for j in range(divide+1): yield Tick()
                self.assertEqual((yield dut.spi_pins.sck_o), 1)
                for j in range(divide+1): yield Tick()
            yield Tick()
            yield Tick()
            yield from self._check_reg(dut, self.REG_STATUS, 1, 1) # full
        sim = Simulator(dut)
        sim.add_clock(1e-5)
        sim.add_testbench(testbench)
        with sim.write_vcd("spi_div_test.vcd", "spi_div_test.gtkw"):
            sim.run()

if __name__ == "__main__":
    unittest.main()

