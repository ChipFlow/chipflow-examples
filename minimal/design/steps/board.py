from amaranth_boards.ulx3s import ULX3S_85F_Platform

from chipflow.platform import BoardStep

from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.cdc import ResetSynchronizer

from ..design import MySoC

class BoardSocWrapper(wiring.Component):
    def __init__(self):
        super().__init__({})
    def elaborate(self, platform):
        m = Module()
        m.submodules.soc = soc = MySoC()

        m.domains += ClockDomain("sync")

        m.d.comb += ClockSignal("sync").eq(platform.request("clk25").i)

        btn_rst = platform.request("button_pwr")
        m.submodules.rst_sync = ResetSynchronizer(arst=btn_rst.i, domain="sync") 

        flash = platform.request("spi_flash", dir=dict(cs='-', copi='-', cipo='-', wp='-', hold='-'))
        # Flash clock requires a special primitive to access in ECP5
        m.submodules.usrmclk = Instance(
            "USRMCLK",
            i_USRMCLKI=soc.flash.clk.o,
            i_USRMCLKTS=ResetSignal(),  # tristate in reset for programmer accesss
            a_keep=1,
        )

        # Flash IO buffers
        m.submodules += Instance(
            "OBZ",
            o_O=flash.cs.io,
            i_I=soc.flash.csn.o,
            i_T=ResetSignal(),
        )

        # Connect flash data pins in order
        data_pins = ["copi", "cipo", "wp", "hold"]
        for i in range(4):
            m.submodules += Instance(
                "BB",
                io_B=getattr(flash, data_pins[i]).io,
                i_I=soc.flash.d.o[i],
                i_T=~soc.flash.d.oe[i],
                o_O=soc.flash.d.i[i]
            )

        # Connect LEDs to GPIO0
        for i in range(8):
            led = platform.request("led", i)
            m.d.comb += led.o.eq(soc.gpio_0.gpio.o[i])

        # Connect UART0
        uart = platform.request("uart")
        m.d.comb += [
            uart.tx.o.eq(soc.uart_0.tx.o),
            soc.uart_0.rx.i.eq(uart.rx.i),
        ]

        return m

class MyBoardStep(BoardStep):
    def __init__(self, config):

        platform = ULX3S_85F_Platform()

        super().__init__(config, platform)

    def build(self):
        my_design = BoardSocWrapper()

        self.platform.build(my_design, do_program=False)
