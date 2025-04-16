from chipflow_lib.platforms.sim import SimPlatform
from chipflow_lib.software.soft_gen import SoftwareGenerator

from amaranth import Module
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out, flipped, connect

from amaranth_soc import csr, wishbone
from amaranth_soc.csr.wishbone import WishboneCSRBridge

from amaranth_orchard.base import SoCID
from amaranth_orchard.memory import QSPIFlash
from amaranth_soc.wishbone.sram import WishboneSRAM
from amaranth_orchard.io import GPIOPeripheral
from amaranth_orchard.io import UARTPeripheral
from amaranth_orchard.io import SPISignature, SPIPeripheral
from amaranth_orchard.io import I2CSignature, I2CPeripheral

from minerva.core import Minerva

from chipflow_lib.platforms import InputPinSignature, OutputPinSignature
# from .ips.pdm import PDMPeripheral

__all__ = ["MySoC"]


class MySoC(wiring.Component):
    def __init__(self):
        # Top level interfaces

        super().__init__({
            "flash": Out(QSPIFlash.Signature()),
            "uart_0": Out(UARTPeripheral.Signature()),
            "gpio_0": Out(GPIOPeripheral.Signature(pin_count=8)),
        })

        # Memory regions:
        self.mem_spiflash_base = 0x00000000
        self.mem_sram_base     = 0x10000000

        # Debug region
        self.debug_base        = 0xa0000000

        # CSR regions:
        self.csr_base          = 0xb0000000
        self.csr_spiflash_base = 0xb0000000

        self.csr_gpio_base     = 0xb1000000
        self.csr_uart_base     = 0xb2000000
        self.csr_soc_id_base   = 0xb4000000

        self.periph_offset     = 0x00100000

        self.sram_size  = 0x400 # 1KiB
        self.bios_start = 0x100000 # 1MiB into spiflash to make room for a bitstream

    def elaborate(self, platform):
        m = Module()

        wb_arbiter  = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8)
        wb_decoder  = wishbone.Decoder(addr_width=30, data_width=32, granularity=8)
        csr_decoder = csr.Decoder(addr_width=28, data_width=8)

        m.submodules.wb_arbiter  = wb_arbiter
        m.submodules.wb_decoder  = wb_decoder
        m.submodules.csr_decoder = csr_decoder

        connect(m, wb_arbiter.bus, wb_decoder.bus)

        # Software

        sw = SoftwareGenerator(rom_start=self.bios_start, rom_size=0x00100000,
                               # place BIOS data in SRAM
                               ram_start=self.mem_sram_base, ram_size=self.sram_size)


        # CPU

        cpu = Minerva(reset_address=self.bios_start, with_muldiv=True)
        wb_arbiter.add(cpu.ibus)
        wb_arbiter.add(cpu.dbus)

        m.submodules.cpu = cpu

        # QSPI Flash

        spiflash = QSPIFlash(addr_width=24, data_width=32)
        wb_decoder .add(spiflash.wb_bus, addr=self.mem_spiflash_base)
        csr_decoder.add(spiflash.csr_bus, name="spiflash", addr=self.csr_spiflash_base - self.csr_base)
        m.submodules.spiflash = spiflash

        connect(m, flipped(self.flash), spiflash.pins)

        sw.add_periph("spiflash",   "SPIFLASH", self.csr_spiflash_base)

        # SRAM

        sram = WishboneSRAM(size=self.sram_size, data_width=32, granularity=8)
        wb_decoder.add(sram.wb_bus, name="sram", addr=self.mem_sram_base)

        m.submodules.sram = sram

        # GPIOs
        m.submodules.gpio = gpio = GPIOPeripheral(pin_count=8)
        csr_decoder.add(gpio.bus, name="gpio_0", addr=self.csr_gpio_base - self.csr_base)
        sw.add_periph("gpio", "GPIO_0", self.csr_gpio_base)

        connect(m, flipped(self.gpio_0), gpio.pins)

        # UART
        m.submodules.uart = uart = UARTPeripheral(init_divisor=int(25e6//115200), addr_width=5)
        csr_decoder.add(uart.bus, name="uart_0", addr=self.csr_uart_base - self.csr_base)
        sw.add_periph("uart", "UART_0", self.csr_uart_base)

        connect(m, flipped(self.uart_0), uart.pins)

        # SoC ID

        soc_id = SoCID(type_id=0xCA7F100F)
        csr_decoder.add(soc_id.bus, name="soc_id", addr=self.csr_soc_id_base - self.csr_base)

        m.submodules.soc_id = soc_id

        # Wishbone-CSR bridge

        wb_to_csr = WishboneCSRBridge(csr_decoder.bus, data_width=32)
        wb_decoder.add(wb_to_csr.wb_bus, name="csr", addr=self.csr_base, sparse=False)

        m.submodules.wb_to_csr = wb_to_csr

        sw.add_periph("soc_id",     "SOC_ID",   self.csr_soc_id_base)

        sw.generate("build/software/generated")

        return m


if __name__ == "__main__":
    from amaranth.back import verilog
    soc_top = MySoC()
    with open("build/soc_top.v", "w") as f:
        f.write(verilog.convert(soc_top, name="soc_top"))
