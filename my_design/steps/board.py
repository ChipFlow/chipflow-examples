from amaranth_boards.ulx3s import ULX3S_85F_Platform

from chipflow_lib.steps.board import BoardStep

from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.cdc import ResetSynchronizer
from amaranth.lib.wiring import connect, flipped
from amaranth.build import Resource, Subsignal, Pins, Attrs

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

        # Because I could only find my old ULX3S....
        platform.add_resources([
            Resource("wifi_gpio", 0, Pins("L2", dir="o"), Attrs(IO_TYPE="LVCMOS33"))
        ])
        wifi_gpio0 = platform.request("wifi_gpio", 0)
        m.d.comb += wifi_gpio0.o.eq(1)

        # Extra IO on headers
        platform.add_resources([
            Resource(
                "expansion",
                0,
                Subsignal("user_spi0_sck",  Pins("0+", conn=("gpio", 0), dir='o')),
                Subsignal("user_spi0_copi", Pins("0-", conn=("gpio", 0), dir='o')),
                Subsignal("user_spi0_cipo", Pins("1+", conn=("gpio", 0), dir='i')),
                Subsignal("user_spi0_csn", Pins("1-", conn=("gpio", 0), dir='o')),

                Subsignal("user_spi1_sck",  Pins("2+", conn=("gpio", 0), dir='o')),
                Subsignal("user_spi1_copi", Pins("2-", conn=("gpio", 0), dir='o')),
                Subsignal("user_spi1_cipo", Pins("3+", conn=("gpio", 0), dir='i')),
                Subsignal("user_spi1_csn", Pins("3-", conn=("gpio", 0), dir='o')),

                Subsignal("i2c0_sda", Pins("4+", conn=("gpio", 0), dir='io')),
                Subsignal("i2c0_scl", Pins("4-", conn=("gpio", 0), dir='io')),

                Subsignal("motor_pwm0_pwm",  Pins("5+", conn=("gpio", 0), dir='o')),
                Subsignal("motor_pwm0_dir",  Pins("5-", conn=("gpio", 0), dir='o')),
                Subsignal("motor_pwm0_stop", Pins("6+", conn=("gpio", 0), dir='i'), Attrs(PULLMODE="DOWN")),

                Subsignal("motor_pwm1_pwm",  Pins("6-", conn=("gpio", 0), dir='o')),
                Subsignal("motor_pwm1_dir",  Pins("7+", conn=("gpio", 0), dir='o')),
                Subsignal("motor_pwm1_stop", Pins("7-", conn=("gpio", 0), dir='i'), Attrs(PULLMODE="DOWN")),

                Subsignal("uart1_rx", Pins("8+", conn=("gpio", 0), dir='i')),
                Subsignal("uart1_tx", Pins("8-", conn=("gpio", 0), dir='o')),

                Subsignal("cpu_jtag_tck", Pins("9+", conn=("gpio", 0), dir='i')),
                Subsignal("cpu_jtag_tms", Pins("9-", conn=("gpio", 0), dir='i')),
                Subsignal("cpu_jtag_tdi", Pins("10+", conn=("gpio", 0), dir='i')),
                Subsignal("cpu_jtag_tdo", Pins("10-", conn=("gpio", 0), dir='o')),
                Subsignal("cpu_jtag_trst", Pins("11+", conn=("gpio", 0), dir='i')),

                Attrs(IO_TYPE="LVCMOS33", PULLMODE="UP"),
            )
        ])

        exp = platform.request("expansion")
        # def _connect_interface(interface, name):
        #     pins = dict()
        #     for pin, width in pins.items():
        #         for i in range(width):
        #             platform_pin = getattr(exp, f"{name}_{pin}{'' if width == 1 else str(i)}")
        #             if hasattr(interface, f"{pin}_i"):
        #                 m.d.comb += getattr(interface, f"{pin}_i")[i].eq(platform_pin.i)
        #             if hasattr(interface, f"{pin}_o"):
        #                 m.d.comb += platform_pin.o.eq(getattr(interface, f"{pin}_o")[i])
        #             if hasattr(interface, f"{pin}_oe"):
        #                 m.d.comb += platform_pin.oe.eq(getattr(interface, f"{pin}_oe")[i])

        # _connect_interface(soc.user_spi_0, "user_spi0")
        # _connect_interface(soc.user_spi_1, "user_spi1")

        # _connect_interface(soc.i2c_0, "i2c0")

        # _connect_interface(soc.motor_pwm0, "motor_pwm0")
        # _connect_interface(soc.motor_pwm1, "motor_pwm1")

        # _connect_interface(soc.uart_1, "uart1")

        # _connect_interface(soc.cpu_jtag, "cpu_jtag")

        return m

class MyBoardStep(BoardStep):
    def __init__(self, config):

        platform = ULX3S_85F_Platform()

        super().__init__(config, platform)

    def build(self):
        my_design = BoardSocWrapper()

        self.platform.build(my_design, do_program=False)
