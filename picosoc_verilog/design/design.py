import os

from chipflow_lib.platforms.sim import SimPlatform

from amaranth import Module, Instance, ClockSignal, ResetSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from chipflow_lib.platforms import (
        GPIOSignature, UARTSignature, QSPIFlashSignature,
        BinaryData, attach_data
    )

__all__ = ["MySoC"]


class MySoC(wiring.Component):
    def __init__(self):
        # Top level interfaces

        super().__init__({
            "flash": Out(QSPIFlashSignature()),
            "uart_0": Out(UARTSignature()),
            "gpio_0": Out(GPIOSignature(pin_count=8)),
        })

    def elaborate(self, platform):
        m = Module()

        base = os.path.dirname(__file__)

        verilog_sources = [
            f"{base}/picosoc_asic_top.v",
            f"{base}/picorv32/picosoc/spimemio.v",
            f"{base}/picorv32/picosoc/simpleuart.v",
            f"{base}/picorv32/picosoc/picosoc.v",
            f"{base}/picorv32/picorv32.v",
        ]

        if platform is not None:
            for verilog_file in verilog_sources:
                with open(verilog_file, 'r') as f:
                    platform.add_file(verilog_file, f)

        m.submodules.soc = soc = Instance("picosoc_asic_top",
            # Clock and reset
            i_clk=ClockSignal(),
            i_resetn=~ResetSignal(),

            # UART
            o_ser_tx=self.uart_0.tx.o,
            i_ser_rx=self.uart_0.rx.i,

            # SPI flash
            o_flash_csb=self.flash.csn.o,
            o_flash_clk=self.flash.clk.o,

            o_flash_io0_oe=self.flash.d.oe[0],
            o_flash_io1_oe=self.flash.d.oe[1],
            o_flash_io2_oe=self.flash.d.oe[2],
            o_flash_io3_oe=self.flash.d.oe[3],

            o_flash_io0_do=self.flash.d.o[0],
            o_flash_io1_do=self.flash.d.o[1],
            o_flash_io2_do=self.flash.d.o[2],
            o_flash_io3_do=self.flash.d.o[3],

            i_flash_io0_di=self.flash.d.i[0],
            i_flash_io1_di=self.flash.d.i[1],
            i_flash_io2_di=self.flash.d.i[2],
            i_flash_io3_di=self.flash.d.i[3],

            # LEDs
            o_leds=self.gpio_0.gpio.o
        )

        # Hardwire GPIO to output enabled
        m.d.comb += self.gpio_0.gpio.oe.eq(0xFF)

        attach_data(self.flash, None, BinaryData(filename="software.bin", offset=0x00100000))

        return m
